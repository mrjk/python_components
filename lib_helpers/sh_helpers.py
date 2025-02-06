import sh

def _exec(command, cli_args=None, logger=None, **kwargs):
    "Execute any command"

    # Check arguments
    cli_args = cli_args or []
    assert isinstance(cli_args, list), f"_exec require a list, not: {type(cli_args)}"

    # Prepare context
    sh_opts = {
        # "_in": sys.stdin,
        # "_out": sys.stdout,
    }
    sh_opts = kwargs or sh_opts

    # Bake command
    cmd = sh.Command(command)
    cmd = cmd.bake(*cli_args)

    # Log command
    if logger:
        cmd_line = [f"{key}='{val}'" for key, val in sh_opts.get("_env", {}).items()]
        # pylint: disable=protected-access
        cmd_line = (
            cmd_line
            + [cmd.__name__]
            + [x.decode("utf-8") for x in cmd._partial_baked_args]
        )
        cmd_line = " ".join(cmd_line)
        logger.exec(cmd_line)  # Support exec level !!!

    # Execute command via sh
    try:
        output = cmd(**sh_opts)
        return output

    except sh.ErrorReturnCode as err:
        # log.error(f"Error while running command: {command} {' '.join(cli_args)}")
        # log.critical (f"Command failed with message:\n{err.stderr.decode('utf-8')}")

        # pprint (err.__dict__)
        # raise error.ShellCommandFailed(err)
        # sys.exit(1)
        raise err

