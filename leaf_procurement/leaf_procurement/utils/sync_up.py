# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import json
import time
import traceback
import requests

import frappe  # type: ignore
from frappe import safe_decode # type: ignore
from frappe.utils import now # type: ignore
from datetime import datetime

error_msg = ""

def create_goods_transfer_note(goods_transfer_note):
    try:
        doc = frappe.new_doc("Goods Transfer Note")
        doc.update(goods_transfer_note)
        doc.custom_is_sync = 1
        doc.insert()
        frappe.db.commit()

        for row in doc.bale_registration_detail:
            if row.bale_barcode:
                update_bale_audit_from_gtn(row.bale_barcode)
                update_gtn_from_bale_audit(row.bale_barcode)
                
        frappe.logger().info(f"[GTN Sync] Created: {doc.name}")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Goods Transfer Note Sync Error")

def update_gtn_from_bale_audit(bale_barcode: str):
    try:
        # Step 1: Get Bale Audit Detail for this barcode
        audit_detail = frappe.db.get_value(
            "Bale Audit Detail",
            {"bale_barcode": bale_barcode, "docstatus": ["<", 2]},
            ["weight", "bale_remarks"],
            as_dict=True
        )
        if not audit_detail:
            return  # No audit record or no GTN linked

        # Step 2: Find GTN Item using bale_barcode and parent = audit_detail.gtn_number
        gtn_item = frappe.db.get_value(
            "Goods Transfer Note Items",
            {"bale_barcode": bale_barcode},
            ["name", "weight"],
            as_dict=True
        )
        if not gtn_item:
            return

        # Step 3: Update the GTN Item's weight from Bale Audit Detail
        frappe.db.set_value("Goods Transfer Note Items", gtn_item.name, {
            "audit_weight": audit_detail.weight,
            "audit_remarks": audit_detail.bale_remarks,
            "weight_difference": float(gtn_item.weight or 0) - float(audit_detail.weight or 0),
        })
        frappe.db.commit()

    except Exception:
        frappe.log_error(
            title="update_gtn_from_bale_audit Failed",
            message=f"Bale Barcode: {bale_barcode}\nError: {frappe.get_traceback()}"
        )

def update_bale_audit_from_gtn(bale_barcode: str):
    try:
        # Find GTN Item with matching bale_barcode
        gtn_item = frappe.db.get_value("Goods Transfer Note Items", {"bale_barcode": bale_barcode}, ["parent", "weight"], as_dict=True)
        if not gtn_item:
            return

        # Get GTN main record fields
        gtn = frappe.db.get_value("Goods Transfer Note", gtn_item.parent, ["name", "tsa_number", "vehicle_number"], as_dict=True)
        if not gtn:
            return

        # Get Bale Audit where this barcode exists
        audit = frappe.get_all(
            "Bale Audit Detail",
            filters={"bale_barcode": bale_barcode, "gtn_number": ["is", "not set"]},
            fields=["parent", "name"]
        )

        for detail in audit:
            try:
                # Update Bale Audit Detail
                frappe.db.set_value("Bale Audit Detail", detail.name, {
                    "gtn_number": gtn.name,
                    "tsa_number": gtn.tsa_number,
                    "truck_number": gtn.vehicle_number,
                    "advance_weight": gtn_item.weight
                })
                frappe.db.commit()
            except Exception as e:
                frappe.log_error(
                    title="Failed to update Bale Audit Detail",
                    message=f"Detail Name: {detail.name}, Error: {frappe.get_traceback()}"
                )

    except Exception as e:
        frappe.log_error(
            title="update_bale_audit_from_gtn Failed",
            message=f"Bale Barcode: {bale_barcode}\nError: {frappe.get_traceback()}"
        )
 
          
#call this from bale audit sync up
def update_audit_details_from_gtn(audit_name: str):
	try:
		doc = frappe.get_doc("Bale Audit", audit_name)
		for row in doc.detail_table:
			if row.bale_barcode:
				update_bale_audit_from_gtn(row.bale_barcode)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Update Audit Details from GTN Error")

#call this from bale audit sync up
def update_gtn_details_from_audit(audit_name: str):
	try:
		doc = frappe.get_doc("Bale Audit", audit_name)
		for row in doc.detail_table:
			if row.bale_barcode:
				update_gtn_from_bale_audit(row.bale_barcode)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Update Audit Details from GTN Error")

#we need to create a job to automate they sync between gtn and bale audit
def update_missing_gtn_in_audits():
	# Find audit detail rows where gtn info is missing
	details = frappe.get_all("Bale Audit Detail", 
		filters={
			"gtn_number": ["is", "null"]
		}, 
		fields=["bale_barcode"]
	)

	for detail in details:
		if detail.bale_barcode:
			update_bale_audit_from_gtn(detail.bale_barcode)

@frappe.whitelist()
def run_gtn_audit_sync_tool():
    doc = frappe.get_doc("GTN Audit Sync Tool")
    try:
        frappe.db.sql("""
            UPDATE `tabBale Audit Detail` AS bad
            JOIN `tabGoods Transfer Note Items` AS gtni
                ON bad.bale_barcode = gtni.bale_barcode
            JOIN `tabGoods Transfer Note` AS gtn
                ON gtni.parent = gtn.name
            SET 
                bad.gtn_number = gtn.name,
                bad.truck_number = gtn.vehicle_number,
                bad.tsa_number = gtn.tsa_number,
                bad.advance_weight = gtni.weight
            WHERE 
                bad.gtn_number IS NULL
                AND bad.bale_barcode IS NOT NULL
        """)
        frappe.db.commit()

        doc.last_run_time = frappe.utils.now()
        doc.run_status = "Completed"
        doc.log = "Batch sync completed using SQL."
        doc.save()
        frappe.db.commit()
        frappe.msgprint("GTN Audit sync completed.")
        
    except Exception as e:
        frappe.log_error("GTN Audit Batch Sync Error", frappe.get_traceback())
        doc.run_status = "Failed"
        doc.log = frappe.get_traceback()
        doc.save()
        frappe.db.commit()
        frappe.throw("Error occurred during sync. Check log.")



def sync_up_worker(values: dict, user=None):
    """Main entry point to sync all selected doctypes."""
    
    settings = frappe.get_cached_doc("Leaf Procurement Settings")
    base_url = settings.instance_url.rstrip('/')
    headers = {
        "Authorization": f"token {settings.api_key}:{settings.api_secret}",
        "Content-Type": "application/json"
    }

    doctypes = {
        "supplier": "Supplier",
        "driver": "Driver",
        "bale_audit": "Bale Audit",
        "bale_registration": "Bale Registration",
        "purchase_invoice": "Purchase Invoice",
        "goods_transfer_note": "Goods Transfer Note",
        "goods_receiving_note": "Goods Receiving Note",
    }

    sync_local_server_instance(parsedurl=base_url, headers=headers, settings=settings)

    for field, doctype in doctypes.items():
        if not values.get(field):
            continue
        sync_records(doctype, base_url, field, headers)
    
    frappe.publish_realtime("sync_complete", {"doctype": "All"}, user=frappe.session.user)


def sync_local_server_instance(parsedurl, headers, settings):
    # local_server_instance(api_key, location, sync_down_date, sync_up_date, users)
    try:
        localsUrl = f"{parsedurl}/api/method/leaf_procurement.api_functions.local_server_instance"
        user_list = frappe.get_all(
            "User",
            fields=["name", "email", 'enabled', 'creation'],
        )
        # Convert datetime to string
        for user in user_list:
            if isinstance(user.get("creation"), datetime):
                user["creation"] = user["creation"].isoformat()
        # user_list = json.loads(user_list.as_json())
        current_datetime = now()

        response = requests.post(localsUrl, headers=headers, json={
            "api_key": settings.api_key,
            "location": settings.location_warehouse,
            "users": user_list,
            "sync_up_date": str(current_datetime),
            "sync_down_date":None,
        })

        error_msg = ""
        if response.status_code not in [200, 201]:
            try:
                error_msg = response.json().get("message", response.text)
            except:
                error_msg = response.text
            
            frappe.log_error(f"❌ Local Server Instance Error", error_msg)
       # frappe.log_error(f"Saved Local Server Instance ", "No error found...")   
    except Exception as e:
        frappe.log_error(f"❌ Local Server Instance Error", traceback.format_exc())
        return

def sync_records(doctype: str, base_url: str, endpoint: str, headers: dict):
    """Sync all unsynced records for a single doctype."""
    try:
        unsynced = frappe.get_all(doctype, filters={"custom_is_sync": 0, "docstatus": ["<", 2]}, pluck="name")
        for name in unsynced:
            sync_single_record(doctype, name, f"{base_url}/api/method/leaf_procurement.api_functions.{endpoint}", headers)
            
    except Exception:
        frappe.log_error(traceback.format_exc(), f"[Sync Error] {doctype}")


def sync_single_record(doctype: str, name: str, url: str, headers: dict):
    """Sync a single document."""
    try:
        doc = frappe.get_doc(doctype, name)
        if doctype == "Bale Registration":
            doc.check_validations = 0
            doc.day_setup = ""
        
        # if doctype == "Purchase Invoice":
        #     # Clear invoice-level cost center (Accounting Dimension)
        #     doc.cost_center = ""

        #     # Clear cost_center in child items
        #     for item in doc.items:
        #         item.cost_center = "Main - SG"

        #     if hasattr(doc, "custom_rejected_items"):
        #         for item in doc.custom_rejected_items:
        #             if hasattr(item, "cost_center"):
        #                 item.cost_center = "Main - SG"
        message = ""
        
        if doctype == "Bale Audit":
            # Check if Audit Day is closed
            audit_day = frappe.db.get_value(
                "Audit Day Setup",
                {"date": doc.date, "location_warehouse": doc.location_warehouse},
                ["name", "status"],
                as_dict=True
            )

            if audit_day and audit_day.status != "Closed":
                log_sync_result(
                    parent_name="Leaf Sync Up",
                    doctype=doctype,
                    docname=name,
                    status="Skipped",
                    message=f"Sync skipped: Audit Day {doc.date} for location {doc.location_warehouse} is not closed."
                )
                return  # Skip sync if not closed

            doc.check_validations = 0
            doc.day_setup = ""
            
        payload = prepare_sync_payload(doc)

        if doctype == "Purchase Invoice":
            payload.pop("custom_barcode_base64", None)

        if doctype == "Goods Transfer Note":
            payload.pop("gtn_barcode", None)
        
        if doctype == "Driver":
            payload.pop("address", None)

        #frappe.log_error(f"[Test] Pay Load:", payload)
        response = requests.post(url, headers=headers, json={doctype.lower().replace(" ", "_"): payload})
        
        if response.status_code in [200, 201]:

            if doctype=="Goods Transfer Note":
                status = "exists"
                try:
                    res_json = response.json()
                except Exception:
                    # Response is not JSON
                    status = "exists"
                else:
                    message = res_json.get("message")
                    
                    if isinstance(message, dict):
                        status = message.get("status", "exists")
                    else:
                        # message is a string or None; treat as already existing
                        status = "exists"             
                        
                if status == "queued":
                    log_sync_result(parent_name="Leaf Sync Up", 
                        doctype=doctype,
                        docname=name, 
                        status= "Queued", 
                        message="GTN has been Queued on Server")
                else:
                    frappe.db.set_value(doctype, name, "custom_is_sync", 1)
                    frappe.db.commit()            

                    log_sync_result(parent_name="Leaf Sync Up", 
                        doctype=doctype,
                        docname=name, 
                        status= "Success", 
                        message="Synced successfully")
                
            else:
                frappe.db.set_value(doctype, name, "custom_is_sync", 1)
                frappe.db.commit()            

                log_sync_result(parent_name="Leaf Sync Up", 
                    doctype=doctype,
                    docname=name, 
                    status= "Success", 
                    message="Synced successfully")    
                            
            if doctype == "Supplier":
                create_supplier_contact(f"{url}/../resource/Contact", headers, payload)
        else:      
            log_sync_error(doctype, name, response)

    except requests.exceptions.RequestException as re:
        # Use response if available (like 400, 500 errors); else fallback to exception
        if hasattr(re, 'response') and re.response is not None:
            log_sync_error(doctype, name, re.response)
        else:
            log_sync_exception("Leaf Sync Up", doctype, name, re)
    except Exception as e:
        log_sync_exception("Leaf Sync Up", doctype, name, e)


def prepare_sync_payload(doc):
    payload = json.loads(doc.as_json())
    payload.update({
        "skip_autoname": True,
        "__islocal": 0,
        "servername": doc.name
    })
    return payload

def log_sync_exception(parent_name, doctype, docname, exc):
    error_message = traceback.format_exc()
    frappe.log_error(f"[Sync Failed] {doctype} - {docname}", error_message)
    log_sync_result(
        parent_name=parent_name,
        doctype=doctype,
        docname=docname,
        status="Failed",
        message=error_message
    )

def log_sync_error(doctype: str, docname: str, response):
    try:
        # Try to extract readable error
        error_msg = response.json().get("message", safe_decode(response.content))
    except Exception:
        try:
            error_msg = response.text
        except Exception:
            error_msg = str(response)

    # Save to error log for admin
    frappe.log_error(f"[Sync Failed] {doctype} - {docname}", error_msg)

    # Save to sync history (summary only)
    log_sync_result(
        parent_name="Leaf Sync Up",  # ✅ Pass actual name dynamically if needed
        doctype=doctype,
        docname=docname,
        status="Failed",
        message=error_msg
    )

def log_sync_result(parent_name, doctype, docname, status, message, retry_count=0):
    log = {
        "doctype": "Leaf Sync Log",
        "doctype_name": doctype,
        "document_name": docname,
        "status": status,
        "message": message,
        "retry_count": retry_count,
        "synced_at": frappe.utils.now_datetime()
    }

    parent = frappe.get_doc("Leaf Sync Up", parent_name)
    parent.append("sync_history", log)
    parent.save(ignore_permissions=True)  # ✅ Needed to persist child rows
    frappe.db.commit()  # ✅ Ensures changes are flushed to DB

def create_supplier_contact(url: str, headers: dict, supplier_doc: dict):
    if not supplier_doc.get("supplier_primary_contact"):
        return

    contact = frappe.get_doc("Contact", supplier_doc["supplier_primary_contact"])
    if contact.custom_is_sync:
        print(f"⚠️ Contact {contact.name} already synced. Skipping...")
        return

    payload = prepare_sync_payload(contact)
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        print(f"✅ Synced Supplier Contact: {contact.name}")
        frappe.db.set_value("Contact", contact.name, "custom_is_sync", 1)
    else:
        try:
            error_msg = "Status Code: " + response.json().get("status_code", response.status_code)  + "Message: " +response.json().get("message", response.text)
        except Exception:
            error_msg = response.text
        frappe.log_error(f"❌ Failed to sync Supplier Contact {contact.name}", error_msg)


def ensure_batch_exists(url: str, headers: dict, batch_no: str, item_code: str, qty: float):
    """Ensure Batch is synced before syncing child transactions."""
    if not batch_no:
        return

    try:
        batch = frappe.get_doc("Batch", batch_no)
        if batch.custom_is_sync:
            print(f"⚠️ Batch {batch.name} already synced. Skipping...")
            return

        payload = prepare_sync_payload(batch)
        response = requests.post(f"{url}/api/resource/Batch", headers=headers, json=payload)

        if response.status_code in [200, 201]:
            print(f"✅ Synced Batch: {batch.name}")
            frappe.db.set_value("Batch", batch.name, "custom_is_sync", 1)
        else:
            try:
                error_msg = response.json().get("message", response.text)
            except Exception:
                error_msg = response.text
            frappe.log_error(f"❌ Failed to sync Batch {batch.name}", error_msg)

    except Exception:
        frappe.log_error(traceback.format_exc(), f"❌ Exception syncing Batch {batch_no} for Item {item_code} Qty {qty}")
