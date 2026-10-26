// asrbench: paced-realtime streaming ASR + endpoint (EOU) latency harness (sherpa-onnx C API).
// Feeds 20 ms chunks at wall-clock rate. Logs wall time of endpoint detection vs. ground-truth EOS.
// usage: asrbench --dir MODELDIR --enc F --dec F --joi F --threads N --wavs DIR --manifest-ids a,b,c
//        --reps R --r1 2.4 --r2 0.5 --seed S --tag T --out jsonl
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include "sherpa-onnx/c-api/c-api.h"

static long long now_ns(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return (long long)t.tv_sec * 1000000000LL + t.tv_nsec; }
static void sleep_until(long long t) { struct timespec s = {t / 1000000000LL, t % 1000000000LL}; clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &s, NULL); }
static long vmhwm_kb(void) { FILE *f = fopen("/proc/self/status", "r"); char l[256]; long v = -1; while (f && fgets(l, sizeof l, f)) if (!strncmp(l, "VmHWM:", 6)) { v = atol(l + 6); break; } if (f) fclose(f); return v; }
static void jesc(FILE *o, const char *s) { for (; *s; s++) { if (*s == '"' || *s == '\\') fputc('\\', o); fputc(*s, o); } }

int main(int argc, char **argv) {
  const char *dir = ".", *enc = 0, *dec = 0, *joi = 0, *wavs = ".", *ids = "", *out = "asr.jsonl", *tag = "";
  const char *eos_list = ""; int threads = 2, reps = 1, seed = 1; float r1 = 2.4f, r2 = 0.5f;
  for (int i = 1; i < argc - 1; i++) {
    if (!strcmp(argv[i], "--dir")) dir = argv[++i]; else if (!strcmp(argv[i], "--enc")) enc = argv[++i];
    else if (!strcmp(argv[i], "--dec")) dec = argv[++i]; else if (!strcmp(argv[i], "--joi")) joi = argv[++i];
    else if (!strcmp(argv[i], "--threads")) threads = atoi(argv[++i]); else if (!strcmp(argv[i], "--wavs")) wavs = argv[++i];
    else if (!strcmp(argv[i], "--ids")) ids = argv[++i]; else if (!strcmp(argv[i], "--eos")) eos_list = argv[++i];
    else if (!strcmp(argv[i], "--reps")) reps = atoi(argv[++i]); else if (!strcmp(argv[i], "--r1")) r1 = atof(argv[++i]);
    else if (!strcmp(argv[i], "--r2")) r2 = atof(argv[++i]); else if (!strcmp(argv[i], "--seed")) seed = atoi(argv[++i]);
    else if (!strcmp(argv[i], "--tag")) tag = argv[++i]; else if (!strcmp(argv[i], "--out")) out = argv[++i];
  }
  char pe[600], pd[600], pj[600], pt[600];
  snprintf(pe, 600, "%s/%s", dir, enc); snprintf(pd, 600, "%s/%s", dir, dec); snprintf(pj, 600, "%s/%s", dir, joi); snprintf(pt, 600, "%s/tokens.txt", dir);
  SherpaOnnxOnlineRecognizerConfig c; memset(&c, 0, sizeof c);
  c.feat_config.sample_rate = 16000; c.feat_config.feature_dim = 80;
  c.model_config.transducer.encoder = pe; c.model_config.transducer.decoder = pd; c.model_config.transducer.joiner = pj;
  c.model_config.tokens = pt; c.model_config.num_threads = threads; c.model_config.provider = "cpu";
  c.decoding_method = "greedy_search"; c.max_active_paths = 4; c.enable_endpoint = 1;
  c.rule1_min_trailing_silence = r1; c.rule2_min_trailing_silence = r2; c.rule3_min_utterance_length = 300.0f;
  long long t0 = now_ns();
  const SherpaOnnxOnlineRecognizer *rec = SherpaOnnxCreateOnlineRecognizer(&c);
  double load_ms = (now_ns() - t0) / 1e6;
  if (!rec) { fprintf(stderr, "create recognizer failed\n"); return 2; }
  // ids and eos lists are parallel, comma-separated; eos = ground-truth EOS sample index
  char *idd = strdup(ids), *eod = strdup(eos_list); char *idv[64], *eov[64]; int n = 0;
  for (char *t = strtok(idd, ","); t; t = strtok(NULL, ",")) idv[n++] = t;
  int m = 0; for (char *t = strtok(eod, ","); t; t = strtok(NULL, ",")) eov[m++] = t;
  int total = n * reps; int *ord = malloc(total * sizeof(int));
  for (int r = 0; r < reps; r++) for (int i = 0; i < n; i++) ord[r * n + i] = i;
  srand(seed); for (int r = 0; r < reps; r++) for (int i = n - 1; i > 0; i--) { int j = rand() % (i + 1); int *a = ord + r * n; int x = a[i]; a[i] = a[j]; a[j] = x; }
  FILE *o = fopen(out, "a");
  const int CH = 320;
  for (int k = 0; k < total; k++) {
    int ix = ord[k]; char fn[700]; snprintf(fn, 700, "%s/%s.wav", wavs, idv[ix]);
    const SherpaOnnxWave *w = SherpaOnnxReadWave(fn); if (!w) { fprintf(stderr, "wav %s\n", fn); continue; }
    long eos = atol(eov[ix]);
    const SherpaOnnxOnlineStream *s = SherpaOnnxCreateOnlineStream(rec);
    long long start = now_ns() + 50000000LL; long fed = 0; long long t_ep = 0, busy = 0, t_first_text = 0, worst = 0; long ep_fed = -1;
    char text[2048] = {0}; int nchunks = 0;
    for (long pos = 0; pos < w->num_samples; pos += CH) {
      int len = (w->num_samples - pos < CH) ? (int)(w->num_samples - pos) : CH;
      sleep_until(start + (long long)(pos + len) * 1000000000LL / 16000);  // chunk fully "spoken" at this wall time
      long long a0 = now_ns();
      SherpaOnnxOnlineStreamAcceptWaveform(s, 16000, w->samples + pos, len); fed = pos + len;
      while (SherpaOnnxIsOnlineStreamReady(rec, s)) SherpaOnnxDecodeOnlineStream(rec, s);
      const SherpaOnnxOnlineRecognizerResult *r = SherpaOnnxGetOnlineStreamResult(rec, s);
      if (r && r->text && strlen(r->text) && strcmp(r->text, text)) { snprintf(text, 2048, "%s", r->text); if (!t_first_text) t_first_text = now_ns(); }
      if (r) SherpaOnnxDestroyOnlineRecognizerResult(r);
      int ep = SherpaOnnxOnlineStreamIsEndpoint(rec, s);
      long long a1 = now_ns(); busy += a1 - a0; if (a1 - a0 > worst) worst = a1 - a0; nchunks++;
      if (ep) { t_ep = a1; ep_fed = fed; break; }
    }
    double lat = -1;
    long long eos_wall = start + eos * 1000000000LL / 16000;
    if (t_ep) lat = (t_ep - eos_wall) / 1e6;
    fprintf(o, "{\"tag\":\"%s\",\"k\":%d,\"id\":\"%s\",\"eos_sample\":%ld,\"endpoint\":%d,\"ep_fed_sample\":%ld,\"eou_minus_eos_ms\":%.1f,"
               "\"premature\":%d,\"first_text_ms_after_start\":%.1f,\"proc_ms_total\":%.1f,\"proc_ms_worst_chunk\":%.2f,\"chunks\":%d,\"vmhwm_kb\":%ld,\"threads\":%d,\"r2\":%.2f,\"load_ms\":%.1f,\"wall\":%lld,\"text\":\"",
            tag, k, idv[ix], eos, t_ep != 0, ep_fed, lat, (t_ep && ep_fed < eos) ? 1 : 0, t_first_text ? (t_first_text - start) / 1e6 : -1.0,
            busy / 1e6, worst / 1e6, nchunks, vmhwm_kb(), threads, r2, load_ms, (long long)time(NULL));
    jesc(o, text); fprintf(o, "\"}\n"); fflush(o);
    SherpaOnnxDestroyOnlineStream(s); SherpaOnnxFreeWave(w);
    usleep(500000);
  }
  fclose(o); SherpaOnnxDestroyOnlineRecognizer(rec); return 0;
}
