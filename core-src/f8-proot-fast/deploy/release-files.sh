# Common file operations for deploy and rollback. Callers hold an exclusive
# lock on the target directory until publication and any recovery finish.

release_files=(bin/proot-fast8 libexec/loader libexec/loader32 auto/proot-fast8 deployed.sha256)

is_fast8() {
  "$1/bin/proot-fast8" --version | grep -E '(^|[[:space:]])5[.]1[.]107[.]92-fast8$' >/dev/null
}

verify_release_backup() (
  cd -- "$1" || exit
  sha256sum --strict -c backup.sha256 || exit
  local path hash
  for path in "${release_files[@]}"; do
    if [[ -f "$path" ]]; then
      hash=$(sha256sum -- "$path") || exit
      grep -Fxq -- "$hash" backup.sha256 || exit
    fi
  done
  [[ -x bin/proot-fast8 && -f libexec/loader ]]
)

prepare_release_files() {
  local source=$1 prepared=$2 path
  shift 2
  mkdir -p -- "$prepared" || return
  for path in "$@"; do
    if [[ -f "$source/$path" ]]; then
      mkdir -p -- "$(dirname -- "$prepared/$path")" || return
      cp -a -- "$source/$path" "$prepared/$path" || return
    fi
  done
}

publish_release_files() {
  local prepared=$1 target=$2 path
  shift 2
  for path in "$@"; do
    if [[ -f "$prepared/$path" ]]; then
      mv -fT -- "$prepared/$path" "$target/$path" || return
    else
      rm -f -- "$target/$path" || return
    fi
  done
}

snapshot_release() (
  local target=$1 backup=$2 path
  local paths=()
  prepare_release_files "$target" "$backup" "${release_files[@]}" || exit
  cd -- "$backup" || exit
  for path in "${release_files[@]}"; do
    if [[ -f "$path" ]]; then paths+=("$path"); fi
  done
  sha256sum -- "${paths[@]}" > backup.sha256 || exit
  verify_release_backup .
)

verify_release_files() {
  local source=$1 target=$2 path
  shift 2
  for path in "$@"; do
    if [[ -f "$source/$path" ]]; then
      cmp -s -- "$source/$path" "$target/$path" || return
    else
      [[ ! -e "$target/$path" && ! -L "$target/$path" ]] || return
    fi
  done
}

finish_release_change() {
  local status=$1 txn=$2 backup=$3 target=$4
  shift 4
  trap - EXIT INT TERM
  if [[ -n "$backup" ]]; then
    if prepare_release_files "$backup" "$txn/recovery" "$@" &&
       publish_release_files "$txn/recovery" "$target" "$@" &&
       verify_release_files "$backup" "$target" "$@"; then
      echo "RECOVERY_PASS restored previous release from $backup" >&2
      if [[ "$status" -eq 0 ]]; then status=10; fi
    else
      echo "RECOVERY_FAILED previous release backup: $backup" >&2
      exit 11
    fi
  fi
  rm -rf -- "$txn" || true
  exit "$status"
}
