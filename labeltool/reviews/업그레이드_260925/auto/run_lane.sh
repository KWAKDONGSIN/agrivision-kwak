#!/usr/bin/env bash
# 260925 업그레이드 사이클의 레인 하나(엔진 하나 + 맡는 태그)를 체크리스트가 끝날 때까지 돌리는 자동 진행기
#   사용: bash run_lane.sh <w1|r1|f1|cx>   (보통은 start_all.sh 가 tmux 로 띄운다)
#   멈춤: auto/STOP · 끝: auto/ALL_DONE · 마감 2026-09-27 12:00 KST
set -u
LANE=$1
T=/data/project/2026summer/platform/work/kwak_dongsin/260916_라벨링툴
K=/data/project/2026summer/kds0206
C=$T/cycles/260925_업그레이드
A=$C/auto
DEADLINE=$(date -d '2026-09-27 12:00' +%s)
ROUND_TIMEOUT=${ROUND_TIMEOUT:-3600}
export PATH="$HOME/.local/node22/bin:$HOME/.npm-global/bin:$HOME/.local/bin:$PATH"
mkdir -p "$A/rounds"

case $LANE in
  w1) ENGINE=claude ACCT=lab      MODEL=claude-opus-5-5  TAGS=코드,시험 PORT=5441 ;;
  r1) ENGINE=claude ACCT=lab      MODEL=claude-sonnet-5  TAGS=팀원,녹취,데이터,조사,제미나이,문서 PORT=5445 ;;
  f1) ENGINE=claude ACCT=personal MODEL=claude-fable-5-1 TAGS=설계,검수,마무리 PORT=5443 ;;
  cx) ENGINE=codex  ACCT=codex    TAGS=코덱스 ;;
  *) echo "모르는 레인 $LANE"; exit 1 ;;
esac

log(){ echo "$(date '+%F %H:%M:%S') [$LANE] $*" >> "$A/$LANE.log"; }
status(){ echo "$(date '+%F %H:%M') [$LANE] $*" >> "$A/STATUS.md"; }
limit_until(){ cat "$A/limit_$ACCT" 2>/dev/null || echo 0; }

log "=== 시작 ($ENGINE/$ACCT ${MODEL:-} · 태그 $TAGS) ==="
while :; do
  date +%s > "$A/$LANE.alive"
  now=$(date +%s)
  [ -e "$A/STOP" ] && { log "STOP → 끝"; exit 0; }
  [ -e "$A/ALL_DONE" ] && { log "ALL_DONE → 끝"; exit 0; }
  [ "$now" -ge "$DEADLINE" ] && { log "마감 → 끝"; status "마감 도달로 멈춤."; exit 0; }

  lu=$(limit_until)
  if [ "$now" -lt "$lu" ]; then
    w=$(( lu - now )); [ $w -gt 1800 ] && w=1800
    log "계정 $ACCT 한도 — $(date -d @$lu '+%m-%d %H:%M') 까지 대기"; sleep $w; continue
  fi

  got=$(python3 "$A/claim.py" claim "$LANE" "$TAGS")
  if [ -z "$got" ]; then
    if [ "$(python3 "$A/claim.py" remaining)" = 0 ]; then touch "$A/ALL_DONE"; status "체크리스트 전부 끝."; exit 0; fi
    sleep 600; continue
  fi
  ID=${got%%$'\t'*}; LINE=${got#*$'\t'}
  out="$A/rounds/$(date +%m%d_%H%M)_${LANE}_${ID}"
  log "항목 $ID 시작"; status "$ID 시작."
  rc=1; limited=0

  if [ "$ENGINE" = claude ]; then
    prompt="$(cat "$A/prompt_common.md")

## 이번 라운드
- 너의 레인: **$LANE** (모델 $MODEL). 모래상자 서버가 필요하면 포트 **$PORT** 만 쓴다.
- 이번 항목(이미 \`[~$LANE]\` 로 잡아 두었다):
  $LINE
- 끝나면 그 줄의 \`[~$LANE]\` 를 \`[x]\` 로 바꾸고 뒤에 \`($LANE $(date +%m-%d))\` 를 붙인다. 못 끝냈으면 \`[ ]\` 로 되돌리고 이유를 context-notes.md 에 적는다."
    cfg=(); [ "$ACCT" = personal ] && cfg=(env CLAUDE_CONFIG_DIR="$HOME/.claude-personal")
    cd "$K" || exit 1
    timeout "$ROUND_TIMEOUT" "${cfg[@]}" "$HOME/.local/bin/claude" -p "$prompt" --model "$MODEL" \
      --permission-mode acceptEdits \
      --allowedTools "Bash Read Write Edit Glob Grep WebSearch WebFetch Skill mcp__jev__* mcp__playwright__*" \
      --max-turns 300 --add-dir "$T" --add-dir "$K" --add-dir /data/project/2026summer \
      > "$out.log" 2>&1
    rc=$?
    if [ "$(stat -c %s "$out.log")" -lt 600 ] && grep -qiE "hit your limit|usage limit|limit reached|resets [0-9]|out of (extra )?usage" "$out.log"; then
      limited=1; r=$(python3 "$A/claim.py" reset "$out.log"); [ "$r" -gt 0 ] || r=$(( $(date +%s) + 1800 ))
      echo "$r" > "$A/limit_$ACCT"; status "계정 $ACCT 한도. $(date -d @$r '+%m-%d %H:%M') 에 이어서."
    fi
  else
    cd "$T" || exit 1
    # 서버에서는 Codex 격리(bwrap)가 안 돼 파일을 못 읽는다 → 코드 차이를 질문에 붙인다
    { cat "$A/prompt_codex.md"; echo; echo "## 이번 항목"; echo "$LINE"; echo; echo '## 코드 차이'; echo '```diff'
      diff -ru -x '_backup_*' -x '__pycache__' -x logs "$C/snapshot_before/app" "$T/app"
      diff -ru -x '_backup_*' -x '__pycache__' "$C/snapshot_before/ai_helper" "$T/ai_helper" 2>/dev/null | grep -v '^Only in'
      echo '```'; } > "$out.prompt"
    timeout "$ROUND_TIMEOUT" codex exec --sandbox read-only --skip-git-repo-check --ephemeral \
      -C "$T" -m gpt-6-astra -c 'model_reasoning_effort="low"' -o "$out.md" - < "$out.prompt" > "$out.log" 2>&1
    rc=$?
    if [ ! -s "$out.md" ] && grep -qiE "usage limit|rate.?limit|quota|429|try again" "$out.log"; then
      limited=1; echo $(( $(date +%s) + 3600 )) > "$A/limit_$ACCT"; status "Codex 한도. 1시간 뒤 다시."
    fi
    if [ "$rc" -eq 0 ] && [ -s "$out.md" ]; then
      cp "$out.md" "$A/${ID}_codex.md"; python3 "$A/claim.py" done "$LANE" "$ID" >/dev/null
      echo "- $(date '+%F %H:%M') [$LANE] $ID 결과 \`auto/${ID}_codex.md\`" >> "$C/context-notes.md"
    fi
  fi

  st=$(python3 "$A/claim.py" state "$ID")
  [ "$st" = "~$LANE" ] && python3 "$A/claim.py" release "$LANE" "$ID" >/dev/null
  log "항목 $ID 끝 rc=$rc 상태=$st 한도=$limited"
  if [ "$st" = x ]; then status "$ID 끝. 남은 항목 $(python3 "$A/claim.py" remaining)개."
  elif [ $limited = 0 ]; then status "$ID 못 끝냄(rc=$rc) — 대기열로."; sleep 300; fi
  sleep 20
done
