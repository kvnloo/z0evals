# sourced on groot. Safety wrappers for z0 phone voice evals.
ADB=~/android/sdk/platform-tools/adb
S22=RFCTA1RZAQY; S25=100.117.226.39:42061
R=~/tmp/voice-evals
LOG=${LOG:-$R/guard.log}
s25_idle() {
  local up last call fg
  up=$($ADB -s $S25 shell 'cut -d. -f1 /proc/uptime' </dev/null | tr -d '\r')
  last=$($ADB -s $S25 shell dumpsys power </dev/null | sed -n 's/.*mLastUserActivityTime[^=]*=\([0-9]*\).*/\1/p' | head -1)
  call=$($ADB -s $S25 shell dumpsys telephony.registry </dev/null | grep -m1 -o 'mCallState=[0-9]' | cut -d= -f2)
  fg=$($ADB -s $S25 shell dumpsys activity activities </dev/null | grep -m1 topResumedActivity | tr -d '\r')
  echo "$(date -Is) s25_idle up=$up last_ms=$last call=$call idle_s=$(( up - last/1000 )) fg=$fg" >> $LOG
  [ "$call" = 0 ] && [ -n "$last" ] && [ $(( up - last/1000 )) -gt 60 ]
}
ph22() { flock -w 900 /tmp/s22-ui.lock $ADB -s $S22 "$@" </dev/null; }
ph25() { s25_idle || { echo BUSY; return 75; }; flock -w 900 /tmp/s25-ui.lock $ADB -s $S25 "$@" </dev/null; }
therm_line() { # $1 serial -> csv: epoch,status,skin,batt_temp_dC,level
  local s=$1
  $ADB -s $s shell 'echo $(date +%s) $(dumpsys thermalservice | grep -m1 "Thermal Status" | tr -dc 0-9) $(dumpsys thermalservice | grep -m1 "mName=SKIN" | sed "s/.*mValue=\([0-9.]*\).*/\1/") $(dumpsys battery | grep -m1 " temperature:" | tr -dc 0-9) $(dumpsys battery | grep -m1 " level:" | tr -dc 0-9)' </dev/null | tr ' ' ',' | tr -d '\r'
}
sampler() { # $1 serial $2 outfile $3 pidfile
  echo epoch,status,skin_c,batt_temp_dC,level > $2
  while :; do therm_line $1 >> $2; sleep 2; done &
  echo $! > $3
}
