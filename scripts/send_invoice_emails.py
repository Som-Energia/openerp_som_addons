# -*- coding: utf-8 -*-
import sys
import click
from erppeek import Client
import logging


def setup_log(instance, filename):
    log_file = filename
    logger = logging.getLogger(instance)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr = logging.FileHandler(log_file)
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)

def get_current_lot(c):
    # gets only current open lot
    return c.GiscedataFacturacioLot.search([('state','=','obert')])

def get_lots(c):
    # gets current lot and previous one
    return c.GiscedataFacturacioLot.search(
        [('state','in',('obert', 'tancat'))], 0, 2, 'data_inici desc'
    )

@click.command()
@click.option('-s', '--server', default='http://localhost',
              help=u'ERP server address')
@click.option('-p', '--port', default=8069, help='ERP server port',
              type=click.INT)
@click.option('-u', '--user', default='admin', help='ERP server user')
@click.option('-w', '--password', help='ERP password' )
@click.option('-d', '--database', help='Nom de la base de dades')
def send_emails(**kwargs):
    setup_log('send_emails', '/tmp/send_emails.log')
    logger = logging.getLogger('send_emails'); print kwargs
    c = Client(
        '{0}:{1}'.format(kwargs['server'], kwargs['port']),
        kwargs['database'],
        kwargs['user'],
        kwargs['password']
    )
    if not c:
        logger.error('Bad ERP connection')
        return
    # lot_ids = get_current_lot(c)
    lot_ids = get_lots(c)
    print lot_ids
    for lot_id in lot_ids:
        lot = c.GiscedataFacturacioLot.get(lot_id)
        logger.info('*** Sending emails of lot {0}:'.format(lot.name))

        context = {'active_id': lot.id}
        wiz = c.WizardFacturesPerEmail.create({},context=context)
        logger.info(wiz.info)
        sys.stdout.write(wiz.info)
        sys.stdout.write('\n')
        res = c.WizardFacturesPerEmail.action_enviar_lot_per_mail([wiz.id], context=context)
        wiz = c.WizardFacturesPerEmail.get(wiz.id)
        logger.info(wiz.info)
        sys.stdout.write(wiz.info)
        sys.stdout.write('\n')


if __name__=='__main__':
    send_emails(auto_envvar_prefix='OPENERP')
