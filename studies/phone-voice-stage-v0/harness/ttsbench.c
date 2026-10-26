// ttsbench: streaming TTS latency harness over sherpa-onnx C API (Pocket TTS).
// One process = one arm (model + threads). Emits one JSON line per trial.
// Usage: ttsbench --model DIR --threads N --texts FILE(tsv: id\tbucket\ttext)
//        --ids id1,id2,... --reps R --gap-ms G --seed S --out trials.jsonl
//        [--ref wav] [--soak-sec T --soak-id ID] [--save-pcm DIR]
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include "sherpa-onnx/c-api/c-api.h"

static long long now_ns(void) {
  struct timespec t;
  clock_gettime(CLOCK_MONOTONIC, &t);
  return (long long)t.tv_sec * 1000000000LL + t.tv_nsec;
}
static long vmhwm_kb(void) {
  FILE *f = fopen("/proc/self/status", "r");
  char line[256];
  long v = -1;
  while (f && fgets(line, sizeof line, f))
    if (!strncmp(line, "VmHWM:", 6)) { v = atol(line + 6); break; }
  if (f) fclose(f);
  return v;
}
typedef struct {
  long long t_call, t_first, t_last, max_gap;
  long long t_prev;
  int chunks;
  long samples;
  float *pcm; long cap;
} Ctx;
static int32_t cb(const float *s, int32_t n, float p, void *arg) {
  Ctx *c = arg;
  long long t = now_ns();
  if (!c->chunks) c->t_first = t;
  else if (t - c->t_prev > c->max_gap) c->max_gap = t - c->t_prev;
  c->t_prev = t; c->t_last = t;
  c->chunks++;
  c->samples += n;
  if (c->pcm) {
    if (c->samples > c->cap) { c->cap = c->samples * 2; c->pcm = realloc(c->pcm, c->cap * sizeof(float)); }
    memcpy(c->pcm + c->samples - n, s, n * sizeof(float));
  }
  return 1;
}
typedef struct { char id[32], bucket[16]; char *text; } Txt;
static Txt T[256]; static int NT;

static void load_texts(const char *fn) {
  FILE *f = fopen(fn, "r"); char *line = NULL; size_t cap = 0;
  while (f && getline(&line, &cap, f) > 0) {
    char *a = strtok(line, "\t"), *b = strtok(NULL, "\t"), *c = strtok(NULL, "\n");
    if (!a || !b || !c) continue;
    snprintf(T[NT].id, 32, "%s", a); snprintf(T[NT].bucket, 16, "%s", b);
    T[NT].text = strdup(c); NT++;
  }
  if (f) fclose(f);
}
static Txt *find(const char *id) { for (int i = 0; i < NT; i++) if (!strcmp(T[i].id, id)) return &T[i]; return NULL; }
static void jesc(FILE *o, const char *s) { for (; *s; s++) { if (*s == '"' || *s == '\\') fputc('\\', o); fputc(*s, o); } }

int main(int argc, char **argv) {
  const char *model = NULL, *texts = NULL, *ids = "", *out = "trials.jsonl", *ref = NULL, *soakid = NULL, *savepcm = NULL, *tag = "";
  int threads = 2, reps = 1, gap_ms = 4000, seed = 1; double soak = 0;
  for (int i = 1; i < argc - 1; i++) {
    if (!strcmp(argv[i], "--model")) model = argv[++i];
    else if (!strcmp(argv[i], "--threads")) threads = atoi(argv[++i]);
    else if (!strcmp(argv[i], "--texts")) texts = argv[++i];
    else if (!strcmp(argv[i], "--ids")) ids = argv[++i];
    else if (!strcmp(argv[i], "--reps")) reps = atoi(argv[++i]);
    else if (!strcmp(argv[i], "--gap-ms")) gap_ms = atoi(argv[++i]);
    else if (!strcmp(argv[i], "--seed")) seed = atoi(argv[++i]);
    else if (!strcmp(argv[i], "--out")) out = argv[++i];
    else if (!strcmp(argv[i], "--ref")) ref = argv[++i];
    else if (!strcmp(argv[i], "--soak-sec")) soak = atof(argv[++i]);
    else if (!strcmp(argv[i], "--soak-id")) soakid = argv[++i];
    else if (!strcmp(argv[i], "--save-pcm")) savepcm = argv[++i];
    else if (!strcmp(argv[i], "--tag")) tag = argv[++i];
  }
  load_texts(texts);
  char p[8][512]; const char *names[7] = {"lm_flow.int8.onnx","lm_main.int8.onnx","encoder.onnx","decoder.int8.onnx","text_conditioner.onnx","vocab.json","token_scores.json"};
  for (int i = 0; i < 7; i++) snprintf(p[i], 512, "%s/%s", model, names[i]);
  SherpaOnnxOfflineTtsConfig cfg; memset(&cfg, 0, sizeof cfg);
  cfg.model.pocket.lm_flow = p[0]; cfg.model.pocket.lm_main = p[1]; cfg.model.pocket.encoder = p[2];
  cfg.model.pocket.decoder = p[3]; cfg.model.pocket.text_conditioner = p[4];
  cfg.model.pocket.vocab_json = p[5]; cfg.model.pocket.token_scores_json = p[6];
  cfg.model.pocket.voice_embedding_cache_capacity = 8;
  cfg.model.num_threads = threads; cfg.model.provider = "cpu";
  long long t0 = now_ns();
  const SherpaOnnxOfflineTts *tts = SherpaOnnxCreateOfflineTts(&cfg);
  long long t_load = now_ns() - t0;
  if (!tts) { fprintf(stderr, "create failed\n"); return 2; }
  int sr = SherpaOnnxOfflineTtsSampleRate(tts);
  char refp[512]; snprintf(refp, 512, "%s/test_wavs/bria.wav", model);
  const SherpaOnnxWave *w = SherpaOnnxReadWave(ref ? ref : refp);
  if (!w) { fprintf(stderr, "ref wav failed\n"); return 3; }
  SherpaOnnxGenerationConfig g; memset(&g, 0, sizeof g);
  g.speed = 1.0f; g.reference_audio = w->samples; g.reference_audio_len = w->num_samples;
  g.reference_sample_rate = w->sample_rate; g.extra = "{\"max_reference_audio_len\": 10.0, \"seed\": 42}";
  FILE *o = fopen(out, "a");
  // schedule
  int sel[256], ns = 0; char *dup = strdup(ids);
  for (char *t = strtok(dup, ","); t; t = strtok(NULL, ",")) sel[ns++] = (find(t) ? (int)(find(t) - T) : -1);
  int total = ns * reps; int *order = malloc(total * sizeof(int));
  for (int r = 0; r < reps; r++) for (int i = 0; i < ns; i++) order[r * ns + i] = sel[i];
  srand(seed);
  for (int r = 0; r < reps; r++) for (int i = ns - 1; i > 0; i--) { int j = rand() % (i + 1); int *a = order + r * ns; int x = a[i]; a[i] = a[j]; a[j] = x; }
  long long soak_end = soak > 0 ? now_ns() + (long long)(soak * 1e9) : 0;
  int ntr = soak > 0 ? 1 << 30 : total;
  // warmup (not logged as trial)
  { Ctx c = {0}; SherpaOnnxGeneratedAudio *a = (void *)SherpaOnnxOfflineTtsGenerateWithConfig(tts, "Warm up run.", &g, cb, &c); if (a) SherpaOnnxDestroyOfflineTtsGeneratedAudio(a); }
  for (int k = 0; k < ntr; k++) {
    Txt *x;
    if (soak > 0) { if (now_ns() >= soak_end) break; x = find(soakid); }
    else x = k >= total || order[k] < 0 ? NULL : &T[order[k]];
    if (!x) continue;
    Ctx c; memset(&c, 0, sizeof c); if (savepcm) { c.cap = 1 << 20; c.pcm = malloc(c.cap * sizeof(float)); }
    long long hw0 = vmhwm_kb();
    c.t_call = now_ns();
    const SherpaOnnxGeneratedAudio *a = SherpaOnnxOfflineTtsGenerateWithConfig(tts, x->text, &g, cb, &c);
    long long t_ret = now_ns();
    double dur = (double)c.samples / sr;
    long nwords = 1; for (const char *s = x->text; *s; s++) if (*s == ' ') nwords++;
    fprintf(o, "{\"tag\":\"%s\",\"k\":%d,\"phase\":\"%s\",\"id\":\"%s\",\"bucket\":\"%s\",\"words\":%ld,\"threads\":%d,\"wall_ns\":%lld,"
            "\"ttfa_ms\":%.2f,\"synth_ms\":%.2f,\"audio_s\":%.3f,\"rtf\":%.4f,\"chunks\":%d,\"max_chunk_gap_ms\":%.2f,\"vmhwm_kb\":%ld,\"vmhwm_before_kb\":%lld,\"model_load_ms\":%.1f,\"ok\":%d,\"text\":\"",
            tag, k, soak > 0 ? "soak" : "scored", x->id, x->bucket, nwords, threads, (long long)time(NULL) * 1000000000LL,
            c.chunks ? (c.t_first - c.t_call) / 1e6 : -1.0, (t_ret - c.t_call) / 1e6, dur, dur > 0 ? ((t_ret - c.t_call) / 1e9) / dur : -1.0,
            c.chunks, c.max_gap / 1e6, vmhwm_kb(), hw0, t_load / 1e6, (a && c.samples > 0) ? 1 : 0);
    jesc(o, x->text); fprintf(o, "\"}\n"); fflush(o);
    if (savepcm && c.samples) { char fn[600]; snprintf(fn, 600, "%s/%s_%d.f32", savepcm, x->id, k); FILE *pf = fopen(fn, "wb"); if (pf) { fwrite(c.pcm, 4, c.samples, pf); fclose(pf); } }
    free(c.pcm);
    if (a) SherpaOnnxDestroyOfflineTtsGeneratedAudio(a);
    if (gap_ms > 0 && soak == 0) usleep(gap_ms * 1000);
  }
  fclose(o);
  SherpaOnnxDestroyOfflineTts(tts);
  return 0;
}
