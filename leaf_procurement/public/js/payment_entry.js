// ============================================================================
// Fingerprint Verification (SecuGen HU20-A) - Payment Entry
//
// Adds a "Verify Fingerprint" button to the Payment Entry form when the
// payee is a Supplier/Grower. Since enrollment (see supplier.js) lets the
// operator pick any one of the 5 right-hand fingers, this first looks up
// WHICH finger was actually enrolled for this Grower and tells the operator
// which one to ask for, then matches a live scan against it - confirming
// the right person is collecting the payment.
//
// Talks to the same local bridge service as supplier.js
// (fingerprint_bridge_service.py on http://localhost:8765). See
// samsons_fingerprint_capture/SETUP_LINUX_DRIVER.md for setup.
//
// The bridge service itself never talks to Frappe - the browser (already
// authenticated) fetches the Grower's stored template and posts it directly
// to the bridge's /verify endpoint alongside the verify request.
// ============================================================================

const SG_WEBAPI_BASE = "http://localhost:8765";
const SG_VERIFY_PATH = "/verify";

const FINGERS = [
	{ id: "right_thumb", key: "thumb", label: __("Right Thumb") },
	{ id: "right_index", key: "index", label: __("Right Index") },
	{ id: "right_middle", key: "middle", label: __("Right Middle") },
	{ id: "right_ring", key: "ring", label: __("Right Ring") },
	{ id: "right_little", key: "little", label: __("Right Little") },
];

// Same geometry as supplier.js, kept in sync for a consistent hand diagram
// (300x340 viewBox, palm + a short wrist stub). Each finger is a tapered
// capsule (wide base, rounded tip) drawn from `base` up to `tip`; the thumb
// is rooted in the palm and rotated outward with `rotate` so it reads as an
// opposable thumb, not a sixth finger.
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

frappe.ui.form.on("Payment Entry", {
	refresh(frm) {
		if (frm.doc.__islocal || frm.doc.party_type !== "Supplier" || !frm.doc.party) return;
		frm.add_custom_button(__("Verify Fingerprint"), () => {
			new FingerprintVerifyDialog(frm);
		});
	},
});

class FingerprintVerifyDialog {
	constructor(frm) {
		this.frm = frm;
		this.attempt = 0;
		this.build();
		this.load_enrolled_template();
	}

	build() {
		this.dialog = new frappe.ui.Dialog({
			title: __("Verify Fingerprint - {0}", [this.frm.doc.party_name || this.frm.doc.party]),
			fields: [{ fieldtype: "HTML", fieldname: "body" }],
			primary_action_label: __("Verify"),
			primary_action: () => this.verify(),
		});
		this.dialog.fields_dict.body.$wrapper.html(this.render_body());
		this.dialog.disable_primary_action();
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
			dots += `<circle class="fp-dot" data-finger="${finger.id}" cx="${cx}" cy="${cy}" r="9"><title>${finger.label}</title></circle>`;
		}
		return `
			<div class="fp-dialog text-center">
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
				<h4 class="fp-current-label">${__("Looking up enrolled finger...")}</h4>
				<div class="fp-preview" style="width:160px;height:200px;border:1px dashed var(--border-color);
					display:flex;align-items:center;justify-content:center;margin:10px auto;border-radius:4px;overflow:hidden;">
					<span class="text-muted fp-preview-placeholder">${__("No scan yet")}</span>
					<img class="fp-preview-img" style="max-width:100%;max-height:100%;display:none;" />
				</div>
				<div class="fp-result" style="font-size:20px;font-weight:600;margin:8px 0;"></div>
				<div class="fp-status text-muted small"></div>
			</div>
			<style>
				.fp-finger { fill: var(--gray-300, #dde2e6); }
				.fp-outline-color { flood-color: var(--gray-600, #74808b); }
				.fp-dot { fill: #fff; stroke: var(--gray-500, #8d99a6); stroke-width: 2; }
				.fp-dot.fp-enrolled { fill: var(--blue-500, #2490ef); stroke: var(--blue-700, #1a56db); }
			</style>
		`;
	}

	set_status(text) {
		this.dialog.$wrapper.find(".fp-status").text(text || "");
	}

	show_preview(base64Image) {
		const $img = this.dialog.$wrapper.find(".fp-preview-img");
		this.dialog.$wrapper.find(".fp-preview-placeholder").hide();
		$img.attr("src", `data:image/png;base64,${base64Image}`).show();
	}

	show_result(matched, score) {
		// SecuGen's matching score is documented (FDx SDK Pro Programming
		// Manual, section 3.13) as ranging 0-199, so it converts to a
		// percentage cleanly - this isn't an arbitrary/open-ended number.
		const percent = Math.round((score / 199) * 100);
		const $result = this.dialog.$wrapper.find(".fp-result");
		if (matched) {
			$result.css("color", "var(--green-500, #2ecc71)").text(`${__("MATCH")} (${percent}%)`);
		} else {
			$result.css("color", "var(--red-500, #e24c4c)").text(`${__("NO MATCH")} (${percent}%)`);
		}
	}

	async load_enrolled_template() {
		this.set_status(__("Loading enrolled fingerprint for {0}...", [this.frm.doc.party]));
		try {
			// Enrollment (supplier.js) lets the operator pick any one of the 5
			// right-hand fingers, so find out which one this Grower actually
			// has on file rather than assuming a fixed finger.
			const files = await frappe.db.get_list("File", {
				filters: [
					["attached_to_doctype", "=", "Supplier"],
					["attached_to_name", "=", this.frm.doc.party],
					["file_name", "like", `${this.frm.doc.party}\_right\_%.tpl`],
				],
				fields: ["file_name", "file_url"],
				limit: 1,
			});

			if (!files || !files.length) {
				this.set_status(
					__("No enrolled fingerprint found for {0}. Capture one on the Supplier form first.", [
						this.frm.doc.party,
					])
				);
				return;
			}

			const file_name = files[0].file_name;
			const finger_id = file_name.slice(`${this.frm.doc.party}_`.length, -".tpl".length);
			this.finger = FINGERS.find((f) => f.id === finger_id);

			if (this.finger) {
				this.dialog.$wrapper.find(".fp-current-label").text(this.finger.label);
				this.dialog.$wrapper.find(`[data-finger="${this.finger.id}"]`).addClass("fp-enrolled");
			}

			const resp = await fetch(files[0].file_url, { credentials: "same-origin" });
			if (!resp.ok) {
				this.set_status(__("Could not download the enrolled fingerprint file."));
				return;
			}
			const buffer = await resp.arrayBuffer();
			this.enrolled_template_b64 = this.array_buffer_to_base64(buffer);
			this.set_status(
				__("Ask {0} to place their {1} on the scanner, then click Verify.", [
					this.frm.doc.party_name || this.frm.doc.party,
					this.finger ? this.finger.label.toLowerCase() : __("enrolled finger"),
				])
			);
			this.dialog.enable_primary_action();
		} catch (e) {
			console.error(e);
			this.set_status(__("Could not load the enrolled fingerprint for this Grower."));
		}
	}

	array_buffer_to_base64(buffer) {
		let binary = "";
		const bytes = new Uint8Array(buffer);
		for (let i = 0; i < bytes.byteLength; i++) {
			binary += String.fromCharCode(bytes[i]);
		}
		return btoa(binary);
	}

	async verify() {
		if (!this.enrolled_template_b64) return;

		this.set_status(__("Place {0} on the scanner...", [this.finger ? this.finger.label : __("finger")]));
		this.dialog.disable_primary_action();
		this.dialog.$wrapper.find(".fp-result").text("");

		let result;
		try {
			const resp = await fetch(`${SG_WEBAPI_BASE}${SG_VERIFY_PATH}`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ template: this.enrolled_template_b64 }),
			});
			result = await resp.json();
		} catch (e) {
			console.error(e);
			this.set_status(
				__(
					"Could not reach the fingerprint scanner service on this PC. Make sure the fingerprint bridge service is running, then try again."
				)
			);
			this.dialog.enable_primary_action();
			return;
		}

		if (!result.success) {
			this.set_status(
				__("Scan failed ({0}). Ask the person to place the finger again.", [
					result.error || __("unknown error"),
				])
			);
			this.dialog.enable_primary_action();
			return;
		}

		this.show_preview(result.image);
		this.show_result(result.matched, result.score);
		this.set_status(__("Saving scan to attachments..."));

		this.attempt++;
		const finger_key = this.finger ? this.finger.id : "unknown";
		const outcome = result.matched ? "match" : "nomatch";
		const base_name = `${this.frm.doc.name}_verify_${finger_key}_${outcome}_${this.attempt}`;
		try {
			await this.upload(`${base_name}.png`, result.image);
			await this.upload(`${base_name}.tpl`, result.template);
		} catch (e) {
			console.error(e);
			// The verification result itself is already shown to the operator -
			// failing to save the attachment shouldn't block them from continuing.
			this.set_status(__("Verified, but the scan image could not be saved as an attachment."));
		}

		this.set_status("");
		this.dialog.enable_primary_action();
		this.dialog.set_primary_action(__("Verify Again"), () => this.verify());
		this.frm.sidebar && this.frm.sidebar.reload_docinfo();
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
