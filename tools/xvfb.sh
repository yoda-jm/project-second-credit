# Sourced by the tools scripts. with_xvfb CMD...: runs CMD on a private Xvfb display (1920x1080), or returns 127
# if Xvfb is not installed.
with_xvfb() {
  command -v Xvfb >/dev/null || return 127
  local n=99
  while [ -e "/tmp/.X11-unix/X$n" ] || [ -e "/tmp/.X$n-lock" ]; do n=$((n + 1)); done
  Xvfb ":$n" -screen 0 1920x1080x24 -nolisten tcp >/dev/null 2>&1 &
  local pid=$!
  for _ in $(seq 50); do [ -e "/tmp/.X11-unix/X$n" ] && break; sleep 0.1; done
  DISPLAY=":$n" "$@"
  local code=$?
  kill "$pid" 2>/dev/null; wait "$pid" 2>/dev/null
  return $code
}
