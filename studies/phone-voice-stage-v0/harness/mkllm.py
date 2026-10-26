import json
p = ("You are a concise voice assistant on a phone. Answer in one short spoken sentence. "
     "The user's calendar shows a dentist appointment on Thursday at two thirty, and a team meeting on Friday at ten. "
     "User: What do I have on Thursday afternoon?\nAssistant:")
open("/home/kvn/tmp/voice-evals/llm60.json","w").write(json.dumps({"prompt":p,"n_predict":1,"cache_prompt":False,"temperature":0,"stream":False}))
print(len(p.split()), "words")
