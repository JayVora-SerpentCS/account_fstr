# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011 Enapps LTD (<http://www.enapps.co.uk>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from openerp.osv import fields, osv
from openerp.tools.translate import _


class account_fstr_wizard(osv.TransientModel):
    """
    Wizard to create financial reports
    """
    _name = 'account_fstr.wizard'
    _description = "Template Print/Preview"
    _columns = {
        'chart_account_id': fields.many2one(
            'account.account', 'Chart of Account',
            help='Select Charts of Accounts',
            required=True, domain=[('parent_id', '=', False)]
        ),
        'company_id': fields.related(
            'chart_account_id', 'company_id', type='many2one',
            relation='res.company', string='Company', readonly=True
        ),
        'fiscalyear': fields.many2one(
            'account.fiscalyear', ('Fiscal year'),
            help=_('Keep empty for all open fiscal years')
        ),
        'period_from': fields.many2one('account.period', _('Start period')),
        'period_to': fields.many2one('account.period', _('End period')),
        'target_move': fields.selection(
            [('posted', _('All Posted Entries')),
             ('all', _('All Entries'))],
            ('Target Moves'), required=True
        ),
        'root_node': fields.many2one(
            'account_fstr.category', _('Root node'), required=True,
        ),
        'hide_zero': fields.boolean(_('Hide accounts with a zero balance')),
        'ignore_special': fields.boolean(_('Ignore Special Periods')),
    }

    def _get_company(self, cr, uid, context=None):
        """
        Get default company for this object
        """
        return self.pool.get('res.company')._company_default_get(
            cr, uid, 'account_fstr.category', context=context
        ),

    def _get_account(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        accounts = self.pool.get('account.account').search(
            cr, uid,
            [('parent_id', '=', False), ('company_id', '=', user.company_id.id)],
            limit=1
        )
        return accounts and accounts[0] or False

    def _get_fiscalyear(self, cr, uid, context=None):
        if context is None:
            context = {}
        now = time.strftime('%Y-%m-%d')
        company_id = False
        ids = context.get('active_ids', [])
        if ids and context.get('active_model') == 'account.account':
            company_id = self.pool.get('account.account').browse(
                cr, uid, ids[0], context=context
            ).company_id.id
        else:  # use current company id
            company_id = self.pool.get('res.users').browse(
                cr, uid, uid, context=context
            ).company_id.id
        domain = [
            ('company_id', '=', company_id),
            ('date_start', '<', now),
            ('date_stop', '>', now)
        ]
        fiscalyears = self.pool.get('account.fiscalyear').search(
            cr, uid, domain, limit=1
        )
        return fiscalyears and fiscalyears[0] or False

    _defaults = {
        'fiscalyear': _get_fiscalyear,
        'company_id': _get_company,
        'chart_account_id': _get_account,
        'target_move': 'posted'
    }

    def onchange_chart_id(
        self, cr, uid, ids, chart_account_id=False, context=None
    ):
        """
        Update fiscal year available values after update chart selection
        """
        res = {}
        if chart_account_id:
            company_id = self.pool.get('account.account').browse(
                cr, uid, chart_account_id, context=context
            ).company_id.id
            now = time.strftime('%Y-%m-%d')
            domain = [
                ('company_id', '=', company_id),
                ('date_start', '<', now),
                ('date_stop', '>', now)
            ]
            fiscalyears = self.pool.get('account.fiscalyear').search(
                cr, uid, domain, limit=1
            )
            res['value'] = {
                'company_id': company_id,
                'fiscalyear_id': fiscalyears and fiscalyears[0] or False
            }
        return res

    def default_get(self, cr, uid, fields, context=None):
        result = super(osv.TransientModel, self).default_get(
            cr, uid, fields, context=context
        )
        result['root_node'] = context.get('active_id', None)
        return result

    def onchange_fiscalyear(self, cr, uid, ids, fiscalyear_id=False, context=None):
        res = {}
        res['value'] = {}
        if fiscalyear_id:
            start_period = end_period = False
            cr.execute('''
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %s
                               ORDER BY p.date_start ASC
                               LIMIT 1) AS period_start
                UNION
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %s
                               AND p.date_start < NOW()
                               ORDER BY p.date_stop DESC
                               LIMIT 1) AS period_stop''', (fiscalyear_id, fiscalyear_id))
            periods = [i[0] for i in cr.fetchall()]
            if periods and len(periods) > 1:
                start_period = periods[0]
                end_period = periods[1]
            res['value'] = {'period_from': start_period, 'period_to': end_period}
        return res

    def open_window(self, cr, uid, ids, context=None):
        """
        Opens chart of Accounts
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of account chart’s IDs
        @return: dictionary of Open account chart window on given fiscalyear and all Entries or posted entries
        """
        if context is None:
            context = {}
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        period_obj = self.pool.get('account.period')
        fy_obj = self.pool.get('account.fiscalyear')
        result = mod_obj.get_object_reference(cr, uid, 'account_fstr', 'action_account_fstr_category_tree')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        result['periods'] = []
        for category in self.browse(cr, uid, ids, context=context):
            if category.period_from and category.period_to:
                result['periods'] = period_obj.build_ctx_periods(cr, uid, category.period_from.id, category.period_to.id)
            result['context'] = str({'fiscalyear': category.fiscalyear.id, 'periods': result['periods'], \
                                    'state': category.target_move})
            if category.fiscalyear:
                result['name'] += ':' + fy_obj.read(cr, uid, [category.fiscalyear.id], context=context)[0]['code']
            print result
            return {
                'view_type': 'tree',
                'view_mode': 'tree',
                'domain': [('id', '=', category.root_node.id)],
                'res_model': 'account_fstr.category',
                'type': 'ir.actions.act_window',
                'tartget': 'new',
                'context': result['context']
            }

    def print_template(self, cr, uid, ids, context={}):
        period_obj = self.pool.get('account.period')
        datas = {'periods': [], 'ids': ids}
        for category in self.browse(cr, uid, ids, context=context):
            if category.period_from and category.period_to:
                context['periods'] = period_obj.build_ctx_periods(cr, uid, category.period_from.id, category.period_to.id)
            datas['context'] = str({'fiscalyear': category.fiscalyear.id,
                                    'periods': datas['periods'],
                                    'state': category.target_move})
        # ignore closing periods if user ticks box in wizard
            if category.ignore_special:
                for period in context['periods']:
                    period_rec = period_obj.browse(cr, uid, period)
                    if period_rec.special is True:
                        # this finds the position 'i' in the list to pop
                        [i for i, x in enumerate(context['periods']) if x == period]
                        context['periods'].pop(i)
            datas['period_from'] = category.period_from.name
            datas['period_to'] = category.period_to.name
            datas['fiscalyear'] = category.fiscalyear.name
            datas['state'] = category.target_move
            context['account_fstr_root_node'] = category.root_node.id
            context['hide_zero'] = category.hide_zero
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account_financial_report.report',
            'datas': datas,
            'context': context,
        }
