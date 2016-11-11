# -*- coding: utf-8 -*-
from django.template.defaulttags import register

OPLATA = u'Op\u0142ata'
WPLATA = u'Wp\u0142aty'
PRZENIESIENIE = u'Przeniesienie'

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def operation_bullet(op_dict, op_date):
    ops = op_dict[op_date]
    if len(ops) == 1 and OPLATA in ops:
        return 'report/bullet_minus_small.png'
    elif sum(ops.values()) > 0:
        return 'report/bullet_plus.png'
    else:
        return 'report/bullet_minus.png'


@register.filter
def operation_balloon(op_dict, op_date):
    ops = op_dict[op_date]
    from pprint import pprint as pp
    op_texts = list()
    if WPLATA in ops:
        op_texts.append(WPLATA + ': %s' % ops[WPLATA])
    if PRZENIESIENIE in ops:
        op_texts.append(PRZENIESIENIE + ': %s' % ops[PRZENIESIENIE])
    if OPLATA in ops:
        op_texts.append(OPLATA + ': %s' % ops[OPLATA])
    if len(op_texts) == 0:
        import pdb; pdb.set_trace()

    return '\n'.join(op_texts)


@register.filter
def has_op(op_dict, op_date):
    return op_date in op_dict

