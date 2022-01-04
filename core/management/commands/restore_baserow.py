from subprocess import CalledProcessError

from django.core.management.base import BaseCommand, CommandError

from core.management.backup.backup_runner import (
    stockcnnBackupRunner,
    add_shared_postgres_command_args,
)


class Command(BaseCommand):
    help = """
        Restores a stockcnn database back_up file generated by the stockcnn
        management command backup_ Only restoring into existing blank databases
        is supported, to restore over an existing database you must DROP and CREATE it
        yourself first.
        To provide the database password you should either have a valid .pgpass file
        containing the password for the requested connection in the expected postgres
        location (see https://www.postgresql.org/docs/current/libpq-pgpass.html) or set
        the PGPASSFILE environment variable.

        WARNING: This command is only safe to run on a database which is not actively
        being updated, not connected to a running version of stockcnn for the
        duration of the back-up and ideally is a blank database unless you manually
        provide additional arguments configuring pg_restore to replace/update.

        This command will be running over multiple split up pg_dump files which contain
        the databases tables in batches.
        """

    def create_parser(self, prog_name, subcommand, **kwargs):
        kwargs["add_help"] = False
        return super().create_parser(prog_name, subcommand, **kwargs)

    def add_arguments(self, parser):
        # Override the help flag so -h can be used for host like pg_dump
        parser.add_argument(
            "--help", action="help", help="Show this help message and exit."
        )
        # The arguments below are meant to match `pg_dump`s arguments in name as this
        # management command is a simple batching/looping wrapper over `pg_dump`.
        parser.add_argument(
            "-j",
            "--jobs",
            type=int,
            dest="jobs",
            default=1,
            help="Run each `pg_restore` command in parallel by restoring this number "
            "of tables simultaneously per batch back-up run. This option reduces "
            "the time of the restore but it also increases the load on the database"
            "server. Please read the `pg_restore` documentation for this argument "
            "for further details.",
        )
        parser.add_argument(
            "-f",
            "--file",
            type=str,
            required=True,
            dest="file",
            help="Restores from the specified file produced by the stockcnn "
            "management command backup_",
        )
        add_shared_postgres_command_args(parser)
        parser.add_argument(
            "additional_pg_restore_args",
            nargs="*",
            help="Any further args specified after a -- will be directly "
            "passed to each call of `pg_restore` which this back_up tool "
            "runs, please see https://www.postgresql.org/docs/11/app-pgdump.html for "
            "all the available options. Please be careful as arguments provided "
            "here will override arguments passed to `pg_restore` internally "
            "by this tool such as -w and -Fd causing undefined and erroneous "
            "behaviour.",
        )

    def handle(self, *args, **options):
        host = options["host"]
        database = options["database"]
        username = options["username"]
        port = options["port"]
        file = options["file"]
        jobs = options["jobs"]
        additional_args = options["additional_pg_restore_args"]

        runner = stockcnnBackupRunner(
            host,
            database,
            username,
            port,
            jobs,
        )
        try:
            runner.restore_stockcnn(file, additional_args)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully restored stockcnn to the database called: {database} "
                )
            )

        except CalledProcessError as e:
            raise CommandError(
                "The back-up failed because of the failure of the following "
                "sub-command, please read the output of the failed command above to "
                "see what went wrong. \n"
                "The sub-command which failed was:\n"
                + " ".join(e.cmd)
                + f"\nIt failed with a return code of: {e.returncode}"
            )
