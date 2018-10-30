import click

from voidkeeper.config import Defaults


def specify_void(voids):
    voids_copy = voids[:]
    fields = Defaults.fields()
    header = Defaults.header()
    header_template = "#  {id} {username} {email} {service}"
    template = "{num}: {id} {username} {email} {service}"

    adjusted_fields = adjust_fields([header] + voids_copy, fields)

    adjusted_header = align_voids([header], adjusted_fields)[0]
    click.secho(
        header_template.format(**adjusted_header),
        bold=True, fg='green', reverse=True)
    index = 0
    for void in align_voids(voids_copy, adjusted_fields):
        void['num'] = index
        click.echo(template.format(**void))
        index += 1

    void_count = len(voids_copy)
    num = click.prompt('Choose void [0..{}]'.format(void_count - 1), type=int)
    if num <= void_count:
        return voids_copy[num]
    click.secho('Aborting!', fg='red')
    return None


def select_void(voidlist, targets):
    voids = voidlist.find(targets)
    if len(voids) == 0 or len(voids) > 10:
        return None
    elif len(voids) > 1:
        return specify_void(voids)
    return voids[0]


def align_str(target_string, width):
    ajust_width = width - len(target_string)
    return "{}{}".format(target_string, " " * ajust_width)


def calc_content_columns(to_adjust_list, fields):
    adjusted_fields = {}
    for field in fields:
        width = len(max((
            str(record.get(field, '')) for record in to_adjust_list), key=len))
        adjusted_fields.update({field: width})
    return adjusted_fields


def calc_table_columns(voidlist, header):
    header_items = header.printable
    pre_columns = calc_content_columns(voidlist.storing, header_items.keys())
    return {col: max(pre_columns.get(col), len(header_items.get(col,0))) for col in pre_columns}


def make_row(void, columns):
    void_dict = void.printable
    return {x: align_str(void_dict.get(x), columns.get(x)) for x in void_dict}


def display_list(voidlist, header):
    columns = calc_table_columns(voidlist, header)
    
    return (make_row(header, columns), [make_row(void, columns) for void in voidlist])


def aquire_password(keeper, ask_password):
    if ask_password:
        return click.prompt('password', type=str, hide_input=True, confirmation_prompt=True)
    return keeper.make_password(13)


def aquire_secrets(secrets_count):
    secrets_list = []
    for _ in range(secrets_count):
        secret = click.prompt('secret name', type=str)
        value = click.prompt('{} is'.format(secret), type=str)
        secrets_list.append({secret: value})
    return secrets_list


def specify_modify_fields(fields):
    if fields:
        return fields.split(',')
    fields_available = Defaults.editable_fields()
    for field, index in zip(fields_available, range(len(fields_available))):
        click.echo('{}: {}'.format(index, field))

    fields_string = click.prompt('Select fields to modify [0..{}]'.format(len(fields_available) - 1), type=str)
    return [fields_available[int(i)] for i in fields_string.split(' ')]


def process_modify_fields(void, fields_list):
    copy_void = void.copy()

    for field in set(fields_list).difference(['secrets', 'id']):
        is_password = field == "password" 
        newvalue = click.prompt('{field}'.format(field=field), default=copy_void.get(field, ''), type=str, confirmation_prompt=is_password)
        if newvalue != '':
            copy_void.update({field: newvalue})

    return copy_void


def modify_old_secrets(secrets):
    new_secrets = []
    for secret in secrets:
        new_secret = {}
        for name, value in secret.items():
            newvalue = click.prompt('{field}'.format(field=name), default=value, type=str)
            new_secret.update({name: newvalue})
        new_secrets.append(new_secret)
    return new_secrets


def append_new_secrets():
    count = click.prompt("How many secrets to append", type=int)
    appended_secrets = aquire_secrets(count)
    return appended_secrets


def process_modify_secrets(void, append_secrets, modify_secrets):
    copy_void = void.copy()
    secrets = copy_void.get('secrets', [])
    if modify_secrets:
        secrets = modify_old_secrets(secrets)
    if append_secrets:
        secrets += append_new_secrets()
    copy_void.update({'secrets': secrets})
    return copy_void

