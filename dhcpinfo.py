#!/usr/bin/env python2
# _*_ coding: utf-8 _*_

from re import compile, match
from argparse import ArgumentParser
from sys import exit


__author__ = 'Antonio Luna'


def op_leases():
    try:
        with open('/var/lib/dhcp/dhcpd.leases', 'r') as dhleases_f:
            dhleases = dhleases_f.readlines()
        return dhleases
    except:
        print ('File "/var/lib/dhcp/dhcpd.leases" does not exists')


def op_conf():
    try:
        with open('/etc/dhcp/dhcpd.conf', 'r') as dhconf_f:
            dhconf = dhconf_f.readlines()
        return dhconf
    except:
        print ('File "/etc/dhcp/dhcpd.conf" does not exists')


# Returns a list with leases sections in dhleases variable.
def leasestrip(leasefile):
    ind_l = []
    leases_regexp = compile(
                     '.*lease \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}.*'
                                )
    key_regexp = compile('^\}')

    counter = 0
    counter_ls = 0
    for cn in leasefile:
        counter = counter + 1
        if leases_regexp.match(cn):
            l_sp = cn.split(' ')
            ind_l.append([l_sp[1], counter])
        if key_regexp.match(cn):
            ind_l[counter_ls].append(counter)
            counter_ls = counter_ls + 1

    return ind_l


# Returns the data in dict format
def dh_dict(lealist, data_var):
    lsdict = {}
    for ls in lealist:
        lsdict[ls[0]] = []
        for i in range(ls[1], ls[2]):
            lsdict[ls[0]].append(
                   data_var[i].replace('\n', '').lstrip(' ').replace(';', '')
                    )
    return lsdict


def rv_strip(conf_var):
    ## Sería ideal meter en la regexp que no hay almohadillas
    ha_regexp = compile('.*host Accountant \{.*')
    hak_regexp = compile('.*\}.*')
    ind_ha = []
    ind_ha_t = []
    ind_hak = []
    counter = 0
    for ha in conf_var:
        if ha_regexp.match(ha):
            ind_ha_t.append(counter)
        if hak_regexp.match(ha):
            ind_hak.append(counter)
        counter = counter + 1

    counter = 0
    for ha in ind_ha_t:
        ind_ha.append([ha])
        hak = len(ind_ha[counter])
        for ll in ind_hak:
            if hak == 1 and ll > ha:
                ind_ha[counter].append(ll)
                hak = len(ind_ha[counter])
        counter = counter + 1
    return ind_ha


def res_dict(reslist, conf_var):
    fix_dict = {}
    hx_st = '[a-fA-F0-9]{2}'
    hw_regexp = compile(
            '.*' + hx_st + '\:' + hx_st + '\:' +
                   hx_st + '\:' + hx_st + '\:' +
                   hx_st + '\:' + hx_st + '.*'
            )

    fix_regexp = compile(
            '.*fixed-address \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}.*'
            )

    for rsv in reslist:
        hw_add = ''
        hw_fix = ''
        hw_add_lst = []
        hw_fix_lst = []

        for lin in range(rsv[0], rsv[1]):
            lin_st = conf_var[lin]

            if hw_regexp.match(lin_st):
                hw_add_lst = lin_st.split(' ')
                hw_add = hw_add_lst[2].replace('\n', '').replace(';', '')

            if fix_regexp.match(lin_st):
                hw_fix_lst = lin_st.split(' ')
                hw_fix = hw_fix_lst[1].replace('\n', '').replace(';', '')

        fix_dict[hw_fix] = hw_add
    return fix_dict


def list_leases(con_dict):
    active_l = []
    leakeys = list(con_dict.keys())
    for i in leakeys:
        l_ip = ''
        l_hw = ''
        for dt in con_dict[i]:
            if dt.startswith('binding state active'):
                l_ip = i
            if dt.startswith('hardware ethernet'):
                l_hw_t = dt.split(' ')
                l_hw = l_hw_t[2].upper()
        if len(l_ip) > 0:
            active_l.append([l_ip, l_hw])
    return active_l


def obt_args():
    arg_dict = {}
    arg_parser = ArgumentParser(
            description='DHCP info tool'
            )

    arg_parser.add_argument(
            '-l', '--list-leases',
            action='store_true',
            help='Show a list of DHCP server leases',
            required=False
            )

    arg_parser.add_argument(
            '-d', '--details',
            type=str,
            help='Show details of a specific ip address',
            required=False
            )

    args = arg_parser.parse_args()
    arg_dict['leases'] = args.list_leases
    arg_dict['dets'] = args.details
    return arg_dict



class dhcp():
    def __init__(self):
        self.config = op_conf()
        self.leases = op_leases()

    def rawleases(self):
        self.ls_list = leasestrip(self.leases)
        self.leases_raw = dh_dict(self.ls_list, self.leases)
        return self.leases_raw

    def reservations(self):
        self.reserv = rv_strip(self.config)
        self.dict_fix = res_dict(self.reserv, self.config)
        return self.dict_fix


if __name__ == '__main__':

    arguments = obt_args()
    app = dhcp()

    leases_t = list_leases(app.rawleases())
    rs = app.reservations()

    if arguments['leases']:
        if len(rs) > 0:
            print ('\nFIXED ADRESSES:\nIP address\t\tHW Address\n')
            for fx in rs:
                print ((('%s\t\t%s') % (fx, rs[fx])))

        if len(leases_t) > 0:
            print ('\nACTIVE LEASES:\nIP address\t\tHW Address\n')
            for ls in leases_t:
                print ((('%s\t\t%s') % (ls[0], ls[1])))

    if arguments['dets'] is not None:
        ip_regexp = compile('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')

        if not ip_regexp.match(arguments['dets']):
            print ('IPv4 invalid')
            exit(1)

        if arguments['dets'] in rs:
            print ((('\n%s is a fixed address assigned to de HW addr: %s\n')
                    % (arguments['dets'], rs[arguments['dets']])))

        if arguments['dets'] not in rs:
            for ls in leases_t:
                if ls[0] == arguments['dets']:
                    print ((('\n%s is a active lease to HW addr: %s\n')
                            % (arguments['dets'], ls[1])))
