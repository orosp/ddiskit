#
#  Completion for ddiskit:
#

_ddiskit()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="prepare_sources generate_spec build_rpm build_iso"

    case "${prev}" in
        prepare_sources)
        COMPREPLY=( $(compgen -f ${cur}) )
            return 0
            ;;
        generate_spec)
        COMPREPLY=( $(compgen -f ${cur}) )
            return 0
            ;;
        build_rpm)
        COMPREPLY=( $(compgen -f ${cur}) )
            return 0
            ;;
        build_iso)
        COMPREPLY=( $(compgen -f ${cur}) )
            return 0
            ;;
        *)
        ;;
    esac

    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
}
complete -F _ddiskit ddiskit
