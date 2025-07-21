import frappe

def boot_session(bootinfo):
    bootinfo.sysdefaults.company_name = "Samsons Group"
    bootinfo.sysdefaults.company_abbr = "SG"