import click

import voidkeeper.utils as utils

from voidkeeper.storage import VoidKeeper, VoidHeader
from voidkeeper.config import Config, Defaults
from voidkeeper.clipboard import Clipboard



pass_keeper = click.make_pass_decorator(VoidKeeper)


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    config = Config()
    state = config.check_state()
    if False in state.values():
        config.restore(state)
    ctx.obj = VoidKeeper(config=config)


@cli.command('list')
@pass_keeper
def show_list(keeper):
    voidlist = keeper.list()
    header = VoidHeader()
    template = Defaults.template()

    (table_header, void_table) = utils.display_list(voidlist, header)
    click.secho(template.format(**table_header), bold=True, fg='green', reverse=True)

    for void in void_table:
        click.echo(template.format(**void))


@cli.command('add')
@click.option('--ask-password', '-p', is_flag=True, default=False,
    help='Set password manualy')
@click.option('--secrets', '-s', default=0, type=int, required=False,
    help='Ask to add secrets')
@pass_keeper
def add_to_list(keeper, ask_password, secrets):
    username = click.prompt('username', type=str)
    email = click.prompt('email', type=str)
    service = click.prompt('service', type=str)
    password = utils.aquire_password(keeper, ask_password)
    secrets_list = utils.aquire_secrets(secrets)

    voidlist = keeper.list()
    voidlist.add({
        'username': username,
        'email': email,
        'service': service,
        'password': password,
        'secrets': secrets_list,
    })
    keeper.store(voidlist)



@cli.command('password')
@click.argument('targets', nargs=-1)
@click.option('--show', '-s', is_flag=True, help="")
@pass_keeper
def get_password(keeper, targets, show):
    voidlist = keeper.list()
    void = utils.select_void(voidlist, targets)
    if void is None:
        click.secho('Cannot find any record, please check your records or be more specific', fg='red')
        return
    password = void.password
    if show:
        click.echo(password)
    else:
        clipboard = Clipboard()
        clipboard.place(password)
        if click.confirm('Clear clipboard?', default=True):
            clipboard.clear()


@cli.command('secrets')
@click.argument('targets', nargs=-1)
@click.option('--show', '-s', is_flag=True, help="")
@pass_keeper
def get_secrets(keeper, targets, show):
    voidlist = keeper.list()
    void = utils.select_void(voidlist, targets)
    if void is None:
        click.secho('Cannot find any void', fg='red')
        return
    secrets = void.secrets
    if len(secrets) == 0:
        click.echo('No secrets for this void')
        return
    for secret, index in zip(secrets, range(len(secrets))):
        [click.echo('{}: {}'.format(index, secret_key)) for secret_key in secret.keys()]

    secret_num = click.prompt('Select secret [0..{}]'.format(len(secrets) - 1), type=int)
    if secret_num > len(secrets) - 1:
        click.secho('Wrong secret selection', fg='red')
        return
    secret = list(secrets[secret_num].values())[0]
    if show:
        click.echo(secret)
    else:
        clipboard = Clipboard()
        clipboard.place(secret)
        if click.confirm('Clear clipboard?', default=True):
            clipboard.clear()


@cli.command('modify')
@click.argument('targets', nargs=-1)
@click.option('--fields', '-f', required=False, default='', help="Comma separated string with fields to modify")
@click.option('--append-secrets', '-as', required=False, default=False, is_flag=True, help="")
@click.option('--modify-secrets', '-ms', required=False, default=False, is_flag=True, help="")
@pass_keeper
def modify_void(keeper, targets, fields, append_secrets, modify_secrets):
    voidlist = keeper.list()
    void = utils.select_void(targets)
    if void is None:
        click.secho('Cannot find any void', fg='red')
        return

    fields_list = False
    if not append_secrets and not modify_secrets:
        fields_list = utils.specify_modify_fields(fields)
    if fields_list:
        diff = set(fields_list).difference(void.printable.keys())
        if diff:
            click.secho('Following fields are not listed in the void: {}'.format(diff), fg='red')
            return
        if 'secrets' in fields_list and not secrets:
            click.secho('Use --secrets option to modify secrets', fg='red')
        if 'id' in fields_list:
            click.secho('You cannot modify ID value', fg='red')
        void = utils.process_modify_fields(void, fields_list)

    if append_secrets or modify_secrets:
        void = utils.process_modify_secrets(void, append_secrets, modify_secrets)
    voidlist.update(void)
    keeper.store(voidlist)

if __name__ == '__main__':
    cli()
