frappe.ui.form.on('Supplier', {
    //custom supplier client script
    onload: function (frm) {
        frm.set_df_property('naming_series', 'hidden', 1);
        if (!frm.doc.custom_nic_number || !frm.doc.custom_location_warehouse) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Leaf Procurement Settings',
                    name: 'Leaf Procurement Settings'
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('custom_company', r.message.company_name);
                        frm.set_value('custom_location_warehouse', r.message.location_warehouse);
                    }
                }
            });
        }
    },
    refresh: function (frm) {
        frm.set_df_property('naming_series', 'hidden', 1);
    },
    validate: function (frm) {
        let cnic = frm.doc.custom_nic_number;
        const cnic_regex = /^\d{5}-\d{7}-\d{1}$/;
        if (cnic) {
            cnic = cnic.replace(/\D/g, '');

            if (cnic.length > 13) {
                cnic = cnic.slice(0, 13);
            }

            if (cnic.length === 13) {
                cnic = `${cnic.slice(0, 5)}-${cnic.slice(5, 12)}-${cnic.slice(12)}`;
            }
            frm.set_value('custom_nic_number', cnic);

            if (cnic && !cnic_regex.test(cnic)) {
                frappe.throw(__('CNIC must be in the format xxxxx-xxxxxxx-x'));
            }
        }
    },
    custom_nic_number: function (frm) {
        let cnic = frm.doc.custom_nic_number;

        if (cnic) {
            // Remove all non-digit characters
            cnic = cnic.replace(/\D/g, '');


            // Limit to 13 digits only
            if (cnic.length > 13) {
                cnic = cnic.slice(0, 13);
            }

            // Auto-format if 13 digits
            if (cnic.length === 13) {
                cnic = `${cnic.slice(0, 5)}-${cnic.slice(5, 12)}-${cnic.slice(12)}`;
            }

            frm.set_value('custom_nic_number', cnic);
        }
    }
});

// ============================================================================
// Fingerprint Capture (SecuGen HU20-A) - one hand, operator's choice of finger
//
// Adds a "Capture Fingerprint" button to the Supplier form. Shows a one-hand
// (right hand, 5 finger) diagram - the operator taps whichever finger the
// person is presenting and captures that one. Saves the scan into the
// Attachments sidebar via frappe.client.attach_file, named after the chosen
// finger so Payment Entry verification can later find it.
//
// SecuGen's official WebAPI service is Windows-only, so on the operator's
// Linux PC this instead talks to our own local bridge service
// (fingerprint_bridge_service.py, built on SecuGen's FDx SDK Pro for Linux),
// which must be running on http://localhost:8765. See
// samsons_fingerprint_capture/SETUP_LINUX_DRIVER.md for setup.
//
// FINGERS ids are also the naming convention used by the Payment Entry
// verification flow to locate the enrolled reference scan/template on a
// Grower's attachments - keep the two in sync if this ever changes.
// ============================================================================

const SG_WEBAPI_BASE = "http://localhost:8765";
const SG_CAPTURE_PATH = "/capture";

const FINGERS = [
	{ id: "right_thumb", key: "thumb", label: __("Right Thumb") },
	{ id: "right_index", key: "index", label: __("Right Index") },
	{ id: "right_middle", key: "middle", label: __("Right Middle") },
	{ id: "right_ring", key: "ring", label: __("Right Ring") },
	{ id: "right_little", key: "little", label: __("Right Little") },
];

// Hand diagram geometry, in a 300x340 viewBox (palm + a short wrist stub, so
// it reads as a hand rather than a cut-off mitten). Each finger is a tapered
// capsule (wide base, rounded tip) drawn from `base` up to `tip`; the thumb
// is drawn the same way then rooted in the palm and rotated outward with
// `rotate` so it reads as an opposable thumb, not a sixth finger. `dot` is
// the tappable fingertip marker, pre-computed at the rotated tip position.
const FINGER_GEOMETRY = {
	thumb: { base: [85, 225], tip: [85, 155], baseW: 32, tipW: 24, rotate: -50, dot: [41, 188] },
	index: { base: [115, 185], tip: [115, 70], baseW: 34, tipW: 24, dot: [115, 82] },
	middle: { base: [150, 185], tip: [150, 40], baseW: 36, tipW: 26, dot: [150, 53] },
	ring: { base: [185, 185], tip: [185, 68], baseW: 34, tipW: 24, dot: [185, 80] },
	little: { base: [216, 185], tip: [216, 105], baseW: 28, tipW: 18, dot: [216, 114] },
};

// Traces one finger as a trapezoid with a rounded tip (before any rotation).
function finger_path(geo) {
	const [bx, by] = geo.base;
	const [tx, ty] = geo.tip;
	const r = geo.tipW / 2;
	return `M ${bx - geo.baseW / 2} ${by} L ${tx - r} ${ty + r} A ${r} ${r} 0 1 1 ${tx + r} ${ty + r} L ${bx + geo.baseW / 2} ${by} Z`;
}

frappe.ui.form.on("Supplier", {
	refresh(frm) {
		if (frm.doc.__islocal) return;
		frm.add_custom_button(__("Capture Fingerprint"), () => {
			new FingerprintCaptureDialog(frm);
		});
	},
});

class FingerprintCaptureDialog {
	constructor(frm) {
		this.frm = frm;
		this.selected = null;
		this.build();
	}

	build() {
		this.dialog = new frappe.ui.Dialog({
			title: __("Capture Fingerprint - {0}", [this.frm.doc.name]),
			fields: [{ fieldtype: "HTML", fieldname: "body" }],
			primary_action_label: __("Capture"),
			primary_action: () => this.capture(),
		});
		this.dialog.fields_dict.body.$wrapper.html(this.render_body());
		this.dialog.disable_primary_action();
		this.dialog.$wrapper.find(".fp-dot").on("click", (e) => {
			this.select_finger($(e.currentTarget).data("finger"));
		});
		this.dialog.show();
	}

	render_body() {
		let fingers = "";
		let dots = "";
		for (const key of ["thumb", "index", "middle", "ring", "little"]) {
			const geo = FINGER_GEOMETRY[key];
			const [cx, cy] = geo.dot;
			const finger = FINGERS.find((f) => f.key === key);
			const transform = geo.rotate ? ` transform="rotate(${geo.rotate} ${geo.base[0]} ${geo.base[1]})"` : "";
			fingers += `<path class="fp-finger" d="${finger_path(geo)}"${transform}></path>`;
			dots += `<circle class="fp-dot" data-finger="${finger.id}" cx="${cx}" cy="${cy}" r="9" style="cursor:pointer;"><title>${finger.label}</title></circle>`;
		}
		return `
			<div class="fp-dialog text-center">
				<div class="text-muted small">${__("Tap the finger being scanned")}</div>
				<svg viewBox="0 0 300 340" width="200" height="227">
					<defs>
						<filter id="fp-hand-outline" x="-30%" y="-30%" width="160%" height="160%">
							<feMorphology in="SourceAlpha" operator="dilate" radius="3" result="dilated"></feMorphology>
							<feFlood class="fp-outline-color" result="outline-color"></feFlood>
							<feComposite in="outline-color" in2="dilated" operator="in" result="outline"></feComposite>
							<feMerge>
								<feMergeNode in="outline"></feMergeNode>
								<feMergeNode in="SourceGraphic"></feMergeNode>
							</feMerge>
						</filter>
					</defs>
					<g filter="url(#fp-hand-outline)">
						<rect class="fp-finger" x="115" y="272" width="70" height="58" rx="10"></rect>
						<rect class="fp-finger" x="70" y="170" width="160" height="110" rx="30"></rect>
						${fingers}
					</g>
					${dots}
				</svg>
				<h4 class="fp-current-label">${__("Select a finger above")}</h4>
				<div class="fp-preview" style="width:160px;height:200px;border:1px dashed var(--border-color);
					display:flex;align-items:center;justify-content:center;margin:10px auto;border-radius:4px;overflow:hidden;">
					<span class="text-muted fp-preview-placeholder">${__("No scan yet")}</span>
					<img class="fp-preview-img" style="max-width:100%;max-height:100%;display:none;" />
				</div>
				<div class="fp-status text-muted small"></div>
			</div>
			<style>
				.fp-finger { fill: var(--gray-300, #dde2e6); }
				.fp-outline-color { flood-color: var(--gray-600, #74808b); }
				.fp-dot { fill: #fff; stroke: var(--gray-500, #8d99a6); stroke-width: 2; }
				.fp-dot.fp-active { fill: var(--blue-500, #2490ef); stroke: var(--blue-700, #1a56db); }
				.fp-dot.fp-done { fill: var(--green-500, #2ecc71); stroke: var(--green-700, #1e8449); }
				.fp-dot.fp-failed { fill: var(--red-500, #e24c4c); stroke: var(--red-700, #a51818); }
			</style>
		`;
	}

	select_finger(id) {
		this.selected = FINGERS.find((f) => f.id === id);
		this.dialog.$wrapper.find(".fp-dot").removeClass("fp-active");
		this.dialog.$wrapper.find(`[data-finger="${id}"]`).addClass("fp-active");
		this.dialog.$wrapper.find(".fp-current-label").text(this.selected.label);
		this.dialog.$wrapper.find(".fp-preview-img").hide();
		this.dialog.$wrapper.find(".fp-preview-placeholder").show();
		this.set_status("");
		this.dialog.set_primary_action(__("Capture"), () => this.capture());
		this.dialog.enable_primary_action();
	}

	set_status(text) {
		this.dialog.$wrapper.find(".fp-status").text(text || "");
	}

	show_preview(base64Image) {
		const $img = this.dialog.$wrapper.find(".fp-preview-img");
		this.dialog.$wrapper.find(".fp-preview-placeholder").hide();
		$img.attr("src", `data:image/png;base64,${base64Image}`).show();
	}

	async capture() {
		if (!this.selected) return;
		const finger = this.selected;
		this.set_status(__("Place {0} on the scanner...", [finger.label]));
		this.dialog.disable_primary_action();

		let result;
		try {
			result = await this.call_webapi();
		} catch (e) {
			console.error(e);
			this.set_status(
				__(
					"Could not reach the fingerprint scanner service on this PC. Make sure the fingerprint bridge service is running, then try again."
				)
			);
			this.mark_dot(finger.id, "fp-failed");
			this.dialog.enable_primary_action();
			return;
		}

		if (!result.success) {
			this.set_status(
				__("Capture failed ({0}). Ask the person to place the finger again.", [
					result.error || __("unknown error"),
				])
			);
			this.mark_dot(finger.id, "fp-failed");
			this.dialog.enable_primary_action();
			return;
		}

		this.show_preview(result.image);
		this.set_status(__("Saving to attachments..."));

		try {
			await this.upload(`${this.frm.doc.name}_${finger.id}.png`, result.image);
			// The template (not the image) is what Payment Entry verification
			// matches against later - saved alongside the PNG so both travel
			// together as normal, unrestricted attachments.
			await this.upload(`${this.frm.doc.name}_${finger.id}.tpl`, result.template);
		} catch (e) {
			console.error(e);
			this.set_status(__("Scan captured but could not be saved as an attachment. Please retry."));
			this.mark_dot(finger.id, "fp-failed");
			this.dialog.enable_primary_action();
			return;
		}

		this.mark_dot(finger.id, "fp-done");
		this.set_status(__("Fingerprint saved for {0}.", [finger.label]));
		this.dialog.enable_primary_action();
		this.dialog.set_primary_action(__("Capture Again"), () => this.capture());
		this.frm.sidebar && this.frm.sidebar.reload_docinfo();
	}

	mark_dot(id, cls) {
		this.dialog.$wrapper
			.find(`[data-finger="${id}"]`)
			.removeClass("fp-active fp-done fp-failed")
			.addClass(cls);
	}

	async call_webapi() {
		const url = `${SG_WEBAPI_BASE}${SG_CAPTURE_PATH}`;
		const resp = await fetch(url);
		return await resp.json();
	}

	upload(filename, base64Data) {
		// frappe.client.attach_file is a built-in whitelisted method - no
		// custom Server Script is needed for the upload itself.
		return frappe.call({
			method: "frappe.client.attach_file",
			args: {
				filename: filename,
				filedata: base64Data,
				doctype: this.frm.doctype,
				docname: this.frm.doc.name,
				decode_base64: 1,
				is_private: 1,
			},
		});
	}
}
