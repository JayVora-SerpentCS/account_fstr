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

from openerp.osv import fields, osv
from openerp.tools.translate import _


class account_fstr_wizard(osv.TransientModel):

    _name = 'account_fstr.wizard'
    _description = "Template Print/Preview"
    _columns = {
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

    def default_get(self, cr, uid, fields, context={}):
        result = super(osv.osv_memory, self).default_get(cr, uid, fields, context=context)
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

    _defaults = {
        'target_move': 'posted'
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
