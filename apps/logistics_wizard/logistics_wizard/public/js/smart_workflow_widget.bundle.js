console.log("SMART WORKFLOW WIDGET SCRIPT LOADED");

$(document).ready(function() {
    // 6-step workflow configuration
    const WORKFLOW_STEPS = [
        { doctype: "Material Request", id: "wiz-Material-Request", slug: "material-request", label: "1. Yêu cầu mua hàng (Material Request)" },
        { doctype: "Purchase Order", id: "wiz-Purchase-Order", slug: "purchase-order", label: "2. Đơn đặt hàng (Purchase Order)" },
        { doctype: "Shipment Tracking", id: "wiz-Shipment-Tracking", slug: "shipment-tracking", label: "3. Theo dõi hành trình (Shipment Tracking)" },
        { doctype: "Purchase Receipt", id: "wiz-Purchase-Receipt", slug: "purchase-receipt", label: "4. Nhận hàng (Purchase Receipt)" },
        { doctype: "Landed Cost Voucher", id: "wiz-Landed-Cost-Voucher", slug: "landed-cost-voucher", label: "5. Phân bổ giá vốn (Landed Cost)" },
        { doctype: "Stock Entry", id: "wiz-Stock-Entry", slug: "stock-entry", label: "6. Nhập kho (Stock Entry)" }
    ];

    const WORKFLOW_DOCTYPES = WORKFLOW_STEPS.map(s => s.doctype);
    let shipmentMap = null;
    let mapPolyline = null;
    let mapMarkers = [];

    // Professional SVG Vehicle Icons
    function get_vehicle_svg(method) {
        if (method === 'Air') {
            return `
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#007AFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.2-1.1.6L2.5 8l6.4 3.3L7 15l-3.3-1.1-1.2 1.3 4.2 3.8 3.8 4.2 1.3-1.2L10.7 18.7l3.7-1.9 3.3 6.4 1.2-1.2-.4-2.6Z"/>
                </svg>
            `;
        } else if (method === 'Ocean') {
            return `
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0055B3" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M2 21c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1 .6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/>
                    <path d="M19.38 20A11.6 11.6 0 0 0 21 14l-9-4-9 4c0 2.9.94 5.34 2.81 7.76"/>
                    <path d="M19 13V7a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v6"/>
                    <path d="M12 10v4"/>
                    <path d="M12 2v3"/>
                </svg>
            `;
        } else {
            return `
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#28a745" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="1" y="3" width="15" height="13" rx="2" ry="2"/>
                    <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/>
                    <circle cx="5.5" cy="18.5" r="2.5"/>
                    <circle cx="18.5" cy="18.5" r="2.5"/>
                </svg>
            `;
        }
    }

    // Inject FAB and Modals
    function inject_fab() {
        if ($('#lw-fab-container').length === 0) {
            let fab_html = `
                <div id="lw-fab-container">
                    <button class="lw-fab" id="lw-fab-main" title="Trợ lý Logistics & Hỗ trợ">
                        <span class="fab-icon">
                            <svg class="lw-lifebuoy-svg" viewBox="0 0 24 24" width="30" height="30" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <defs>
                                    <linearGradient id="lw-apple-blue-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                                        <stop offset="0%" stop-color="#0A84FF"/>
                                        <stop offset="50%" stop-color="#0071E3"/>
                                        <stop offset="100%" stop-color="#0055D4"/>
                                    </linearGradient>
                                    <filter id="lw-liquid-glow" x="-20%" y="-20%" width="140%" height="140%">
                                        <feDropShadow dx="0" dy="1.5" stdDeviation="1.5" flood-color="#0071E3" flood-opacity="0.3"/>
                                    </filter>
                                </defs>
                                <g filter="url(#lw-liquid-glow)">
                                    <circle cx="12" cy="12" r="9.2" stroke="url(#lw-apple-blue-grad)" stroke-width="2.3"/>
                                    <circle cx="12" cy="12" r="3.8" stroke="url(#lw-apple-blue-grad)" stroke-width="2.3"/>
                                    <line x1="5.5" y1="5.5" x2="9.3" y2="9.3" stroke="url(#lw-apple-blue-grad)" stroke-width="2.3" stroke-linecap="round"/>
                                    <line x1="18.5" y1="5.5" x2="14.7" y2="9.3" stroke="url(#lw-apple-blue-grad)" stroke-width="2.3" stroke-linecap="round"/>
                                    <line x1="18.5" y1="18.5" x2="14.7" y2="14.7" stroke="url(#lw-apple-blue-grad)" stroke-width="2.3" stroke-linecap="round"/>
                                    <line x1="5.5" y1="18.5" x2="9.3" y2="14.7" stroke="url(#lw-apple-blue-grad)" stroke-width="2.3" stroke-linecap="round"/>
                                </g>
                            </svg>
                        </span>
                        <span class="fab-close-icon">✕</span>
                    </button>
                    <div id="lw-fab-menu">
                        <button class="lw-fab lw-sub-fab" id="lw-fab-workflow" data-tooltip="Tiến trình (Workflow)">📋</button>
                        <button class="lw-fab lw-sub-fab" id="lw-fab-shipment" data-tooltip="Hành trình (Shipment)">🚚</button>
                        <button class="lw-fab lw-sub-fab" id="lw-fab-ai" data-tooltip="AI Chat">🤖</button>
                    </div>
                </div>

                <!-- Popup: Workflow -->
                <div class="lw-popup" id="lw-popup-workflow">
                    <div class="lw-popup-header">
                        Tiến trình chứng từ XNK
                        <span class="lw-popup-close" data-target="#lw-popup-workflow">✖</span>
                    </div>
                    <div class="lw-popup-body">
                        <ul class="lw-step-list">
                            ${WORKFLOW_STEPS.map(s => `
                                <li class="lw-step-item" id="${s.id}">
                                    <span class="wiz-check-badge"></span>
                                    <a href="/app/${s.slug}">${s.label}</a>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                </div>

                <!-- Popup: Shipment (Map & Timeline) -->
                <div class="lw-popup lw-popup-large" id="lw-popup-shipment">
                    <div class="lw-popup-header">
                        <span>🗺️ Bản đồ & Hành trình Vận chuyển Toàn cầu</span>
                        <span class="lw-popup-close" data-target="#lw-popup-shipment">✖</span>
                    </div>
                    <div class="lw-popup-body" id="lw-shipment-content">
                        <div style="text-align: center; color: #8d99a6; padding: 25px 0;">
                            Đang tải thông tin hành trình...
                        </div>
                    </div>
                </div>

                <!-- Popup: AI Chat -->
                <div class="lw-popup" id="lw-popup-ai">
                    <div class="lw-popup-header">
                        Trợ lý AI Logistics & Hải quan
                        <span class="lw-popup-close" data-target="#lw-popup-ai">✖</span>
                    </div>
                    <div class="lw-popup-body" style="text-align: center; padding: 30px 15px;">
                        <div style="font-size: 44px; margin-bottom: 12px;">🤖</div>
                        <h4 style="margin:0 0 10px 0; color: #1f272e;">Trợ lý RAG Hải quan</h4>
                        <p style="color: #6c757d; font-size: 13px; line-height: 1.5; margin: 0;">
                            Hệ thống AI RAG hỗ trợ tra cứu văn bản pháp luật Hải quan và đề xuất mã HS Code đang kết nối!
                        </p>
                    </div>
                </div>
            `;
            $('body').append(fab_html);

            // Bind Events
            $('#lw-fab-main').on('click', function() {
                $(this).toggleClass('active');
                if ($(this).hasClass('active')) {
                    $('#lw-fab-menu').addClass('show');
                } else {
                    $('#lw-fab-menu').removeClass('show');
                    $('.lw-popup').hide();
                }
            });

            $('.lw-sub-fab').on('click', function() {
                let target = $(this).attr('id').replace('lw-fab-', 'lw-popup-');
                $('.lw-popup').hide();
                $('#' + target).show();
                
                if (target === 'lw-popup-shipment') {
                    open_shipment_view();
                }
            });

            $('.lw-popup-close').on('click', function() {
                $($(this).data('target')).hide();
                if (shipmentMap) {
                    try { shipmentMap.remove(); } catch(e) {}
                    shipmentMap = null;
                }
            });
        }
    }

    // Determine what to show in the Shipment Popup
    function open_shipment_view() {
        let route = (typeof frappe !== 'undefined' && frappe.get_route) ? frappe.get_route() : [];
        if (route && route[0] === 'Form' && route[1] && ['Purchase Order', 'Shipment Tracking', 'Purchase Receipt'].includes(route[1]) && route[2]) {
            load_shipment_map(route[2], route[1]);
        } else {
            show_active_shipments_list();
        }
    }

    // List all active shipments
    function show_active_shipments_list() {
        let $content = $('#lw-shipment-content');
        $content.html(`
            <div style="text-align: center; padding: 20px; color: #6c757d;">
                <div class="spinner-border text-primary" role="status"></div>
                <div style="margin-top: 10px;">Đang tải danh sách lô hàng đang vận chuyển...</div>
            </div>
        `);

        frappe.call({
            method: 'logistics_wizard.api.get_active_shipments',
            callback: function(r) {
                if (r.message && r.message.status === 'success') {
                    let pos = r.message.data || [];
                    if (pos.length === 0) {
                        $content.html(`
                            <div style="text-align: center; padding: 35px 20px; color: #8d99a6;">
                                <div style="font-size: 32px; margin-bottom: 8px;">📦</div>
                                <strong>Không có đơn hàng nào đang vận chuyển.</strong>
                                <p style="font-size: 12px; margin-top: 6px;">Hãy tạo Purchase Order hoặc mở một đơn hàng để xem bản đồ hành trình.</p>
                            </div>
                        `);
                        return;
                    }

                    let html = `
                        <div style="margin-bottom: 12px;">
                            <strong style="color: #1f272e; font-size: 14px;">Danh sách Lô hàng Quốc tế Đang Vận chuyển:</strong>
                            <div style="font-size: 12px; color: #6c757d;">Nhấn vào đơn hàng để xem bản đồ lộ trình trực tiếp:</div>
                        </div>
                        <div class="lw-shipment-list" style="display: flex; flex-direction: column; gap: 8px;">
                    `;

                    pos.forEach(p => {
                        html += `
                            <div class="lw-shipment-item" data-name="${p.name}" style="padding: 12px 14px; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; cursor: pointer; transition: all 0.2s;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <strong style="color: #007AFF; font-size: 13px;">${p.name}</strong>
                                    <span class="badge" style="background: #e7f1ff; color: #007AFF; font-weight: 500; font-size: 11px;">${p.status}</span>
                                </div>
                                <div style="font-size: 12px; color: #495057; margin-top: 4px;">
                                    <strong>Nhà cung cấp:</strong> ${p.supplier_name || 'N/A'}
                                </div>
                            </div>
                        `;
                    });

                    html += `</div>`;
                    $content.html(html);

                    $('.lw-shipment-item').hover(
                        function() { $(this).css({ 'background': '#eef5ff', 'border-color': '#b8d5fd' }); },
                        function() { $(this).css({ 'background': '#f8f9fa', 'border-color': '#e9ecef' }); }
                    ).on('click', function() {
                        let name = $(this).data('name');
                        load_shipment_map(name, 'Purchase Order');
                    });
                } else {
                    $content.html('<div style="text-align: center; color: red; padding: 20px;">Lỗi tải danh sách vận chuyển.</div>');
                }
            }
        });
    }

    // Load Map & Timeline for a specific document
    function load_shipment_map(docname, doctype) {
        let $content = $('#lw-shipment-content');
        $content.html(`
            <div class="lw-map-panel">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <button class="btn btn-xs btn-default" id="lw-btn-back-shipments">← Quay lại danh sách</button>
                    <div style="text-align: right;">
                        <span style="font-size: 11px; color: #6c757d;">${doctype}:</span>
                        <strong style="color: #007AFF; font-size: 13px; margin-left: 4px;">${docname}</strong>
                    </div>
                </div>

                <!-- Map Container -->
                <div id="shipment-map" style="width: 100%; height: 350px; border-radius: 10px; background: #e5e5ea; border: 1px solid #ced4da;"></div>

                <!-- Info Box -->
                <div class="lw-map-info" id="lw-map-info-text" style="padding: 10px 14px; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; font-size: 13px;">
                    <span class="text-muted">Đang phân tích dữ liệu tọa độ địa lý và dựng lộ trình...</span>
                </div>

                <!-- Detailed Timeline -->
                <div>
                    <div style="font-weight: 600; font-size: 13px; color: #343a40; margin-bottom: 8px;">
                        Lộ trình Vận chuyển Chi tiết (Transit Checkpoints):
                    </div>
                    <div id="lw-timeline-container" style="max-height: 180px; overflow-y: auto;"></div>
                </div>
            </div>
        `);

        $('#lw-btn-back-shipments').on('click', function() {
            if (shipmentMap) {
                try { shipmentMap.remove(); } catch(e) {}
                shipmentMap = null;
            }
            show_active_shipments_list();
        });

        // Call backend API
        frappe.call({
            method: 'logistics_wizard.api.get_shipment_tracking',
            args: { docname: docname, doctype: doctype },
            callback: function(r) {
                if (r.message && r.message.status === 'success') {
                    init_map(r.message.data, docname, doctype);
                } else {
                    $('#lw-map-info-text').html(`<span style="color: #d9534f;">${r.message ? r.message.message : "Không thể tải thông tin lộ trình."}</span>`);
                }
            }
        });
    }

    // Initialize Leaflet Map
    function init_map(data, docname, doctype) {
        const Leaflet = window.L || window.leaflet;
        if (!Leaflet) {
            $('#lw-map-info-text').html('<span style="color: red;">Thư viện bản đồ (Leaflet) chưa được tải.</span>');
            return;
        }

        if (shipmentMap) {
            try { shipmentMap.remove(); } catch(e) {}
            shipmentMap = null;
        }

        // Clean slate
        mapMarkers = [];
        mapPolyline = null;

        // Create Map
        shipmentMap = Leaflet.map('shipment-map', {
            zoomControl: true,
            attributionControl: true
        }).setView([20.0, 150.0], 3);

        // OpenStreetMap / Wikimedia tile layer (NO API KEY REQUIRED, NO WATERMARK)
        Leaflet.tileLayer('https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors',
            maxZoom: 18
        }).addTo(shipmentMap);

        let coords = data.route || data.full_route || [];
        if (!coords || coords.length === 0) {
            $('#lw-map-info-text').html('<span class="text-muted">Chưa có tọa độ nào được ghi nhận cho đơn hàng này.</span>');
            return;
        }

        // 1. Draw Polyline
        let lineStyle = {
            color: data.method === 'Air' ? '#007AFF' : (data.method === 'Ocean' ? '#0055B3' : '#28a745'),
            weight: 3.5,
            opacity: 0.85,
            dashArray: data.method === 'Air' ? '6, 8' : (data.method === 'Ocean' ? '8, 4' : '')
        };

        mapPolyline = Leaflet.polyline(coords, lineStyle).addTo(shipmentMap);
        try {
            shipmentMap.fitBounds(mapPolyline.getBounds(), { padding: [40, 40], maxZoom: 8 });
        } catch(e) {}

        // 2. Origin Marker (USA / Supplier)
        let originCoord = coords[0];
        let originIcon = Leaflet.divIcon({
            className: 'custom-origin-icon',
            html: `<div style="background: #28a745; color: white; border-radius: 50%; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.3);">A</div>`,
            iconSize: [26, 26],
            iconAnchor: [13, 13]
        });
        let origMarker = Leaflet.marker(originCoord, { icon: originIcon }).addTo(shipmentMap);
        origMarker.bindPopup(`<b>Điểm xuất phát (Origin):</b><br>${coords[0][0].toFixed(2)}, ${coords[0][1].toFixed(2)}`);

        // 3. Destination Marker (Vietnam / Warehouse)
        let destCoord = coords[coords.length - 1];
        let destIcon = Leaflet.divIcon({
            className: 'custom-dest-icon',
            html: `<div style="background: #dc3545; color: white; border-radius: 50%; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.3);">B</div>`,
            iconSize: [26, 26],
            iconAnchor: [13, 13]
        });
        let dstMarker = Leaflet.marker(destCoord, { icon: destIcon }).addTo(shipmentMap);
        dstMarker.bindPopup(`<b>Điểm đến (Destination):</b><br>${destCoord[0].toFixed(2)}, ${destCoord[1].toFixed(2)}`);

        // 4. Moving Vehicle Marker (Current position)
        let currentPos = coords[coords.length - 1];
        if (data.progress < 1.0 && coords.length > 1) {
            // Position vehicle along the route
            currentPos = coords[Math.min(coords.length - 1, Math.floor(coords.length * (data.progress || 0.5)))];
        }

        let vehicleIcon = Leaflet.divIcon({
            className: 'custom-vehicle-icon',
            html: `
                <div style="background: white; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; box-shadow: 0 3px 10px rgba(0,0,0,0.25); border: 2.5px solid ${data.method === 'Air' ? '#007AFF' : (data.method === 'Ocean' ? '#0055B3' : '#28a745')};">
                    ${get_vehicle_svg(data.method)}
                </div>
            `,
            iconSize: [40, 40],
            iconAnchor: [20, 20]
        });

        let vehMarker = Leaflet.marker(currentPos, { icon: vehicleIcon, zIndexOffset: 1000 }).addTo(shipmentMap);
        vehMarker.bindPopup(`<b>Vị trí hiện tại:</b><br>${data.current_location || 'Đang vận chuyển'}`).openPopup();

        // 5. Update Info Text
        let methodBadge = data.method === 'Air' ? '✈️ Đường hàng không (Air)' : (data.method === 'Ocean' ? '🚢 Đường biển (Ocean)' : '🚚 Đường bộ (Road)');
        let infoHtml = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span><strong>Phương thức:</strong> ${methodBadge}</span>
                <span class="badge" style="background: #e7f1ff; color: #007AFF;">${data.status_text}</span>
            </div>
            <div><strong>Vị trí hiện tại:</strong> <span style="color: #007AFF; font-weight: 500;">${data.current_location}</span></div>
        `;
        $('#lw-map-info-text').html(infoHtml);

        // 6. Render Checkpoints in Timeline
        render_checkpoints_timeline(docname, doctype);

        // Invalidate map size after animation/popup display
        setTimeout(() => {
            if (shipmentMap) {
                shipmentMap.invalidateSize();
            }
        }, 300);
    }

    // Render Timeline below the map
    function render_checkpoints_timeline(docname, doctype) {
        let $timeline = $('#lw-timeline-container');
        
        // If window.cur_frm is this document and has transit_route
        if (window.cur_frm && cur_frm.doc && (cur_frm.doc.name === docname) && cur_frm.doc.transit_route && cur_frm.doc.transit_route.length > 0) {
            draw_timeline_items(cur_frm.doc.transit_route, $timeline);
            return;
        }

        // Otherwise fetch via frappe.db.get_doc
        let targetDocType = doctype;
        let targetDocName = docname;

        if (doctype === 'Purchase Order') {
            frappe.db.get_value('Shipment Tracking', { purchase_order: docname }, 'name').then(r => {
                if (r && r.message && r.message.name) {
                    frappe.db.get_doc('Shipment Tracking', r.message.name).then(doc => {
                        draw_timeline_items(doc.transit_route || [], $timeline);
                    });
                } else {
                    $timeline.html('<div style="color: #8d99a6; font-size: 12px; padding: 8px 0;">Chưa liên kết phiếu Shipment Tracking hoặc chưa có lộ trình chi tiết.</div>');
                }
            });
        } else if (doctype === 'Shipment Tracking') {
            frappe.db.get_doc('Shipment Tracking', docname).then(doc => {
                draw_timeline_items(doc.transit_route || [], $timeline);
            });
        } else {
            $timeline.html('<div style="color: #8d99a6; font-size: 12px; padding: 8px 0;">Không có dữ liệu lộ trình.</div>');
        }
    }

    function draw_timeline_items(routes, $container) {
        if (!routes || routes.length === 0) {
            $container.html('<div style="color: #8d99a6; font-size: 12px; padding: 8px 0;">Chưa có trạm lộ trình nào.</div>');
            return;
        }

        let html = '<div class="lw-timeline" style="margin-top: 5px;">';
        routes.forEach((r, idx) => {
            let isLast = (idx === routes.length - 1);
            html += `
                <div class="lw-timeline-item done">
                    <div class="lw-timeline-date" style="font-size: 11px; color: #6c757d;">${r.date || ''}</div>
                    <div class="lw-timeline-title" style="font-weight: 600; font-size: 13px; color: #1f272e;">${r.activity || ''}</div>
                    <div class="lw-timeline-desc" style="font-size: 12px; color: #495057;">📍 ${r.location || ''}</div>
                </div>
            `;
        });
        html += '</div>';
        $container.html(html);
    }

    // Reset workflow step UI
    function reset_workflow_ui() {
        WORKFLOW_STEPS.forEach(step => {
            let $li = $('#' + step.id);
            if ($li.length) {
                $li.removeClass('wiz-step-completed wiz-step-current wiz-step-pending');
                $li.find('.wiz-check-badge').html('');
                let $a = $li.find('a');
                $a.attr('href', '/app/' + step.slug);
                $a.text(step.label);
            }
        });
    }

    // Update state based on API response
    function render_chain_status(steps) {
        if (!steps || !steps.length) return;

        steps.forEach(step_data => {
            let step_cfg = WORKFLOW_STEPS.find(s => s.doctype === step_data.doctype);
            if (!step_cfg) return;

            let $li = $('#' + step_cfg.id);
            if (!$li.length) return;

            let label_text = step_data.label || step_cfg.label;
            let url = step_data.url || ('/app/' + step_cfg.slug);
            let $a = $li.find('a');
            $a.attr('href', url);
            $a.text(label_text);

            if (step_data.completed) {
                $li.addClass('wiz-step-completed');
                $li.find('.wiz-check-badge').html('✔');
            } else if (step_data.is_current) {
                $li.addClass('wiz-step-current');
            } else {
                $li.addClass('wiz-step-pending');
            }

            if (step_data.is_current) {
                $li.addClass('wiz-step-current');
            }
        });
    }

    // Fetch and update workflow status
    function update_widget_state() {
        inject_fab();
        if (typeof frappe === 'undefined' || !frappe.get_route) return;

        let route = frappe.get_route();
        if (!route || !route.length) return;

        if (route[0] === "Form" && route[1] && WORKFLOW_DOCTYPES.includes(route[1]) && route[2]) {
            let doctype = route[1];
            let docname = route[2];

            frappe.call({
                method: "logistics_wizard.api.get_workflow_chain_status",
                args: { doctype: doctype, docname: docname },
                callback: function(r) {
                    reset_workflow_ui();
                    if (r && r.message && r.message.success) {
                        render_chain_status(r.message.steps);
                    }
                }
            });
        } else if (route[0] === "List" && route[1] && WORKFLOW_DOCTYPES.includes(route[1])) {
            reset_workflow_ui();
            let doctype_id = "wiz-" + route[1].replace(/\s+/g, '-');
            $('#' + doctype_id).addClass('wiz-step-current');
        } else {
            reset_workflow_ui();
        }
    }

    // Bind route change event
    if (typeof frappe !== 'undefined' && frappe.router) {
        frappe.router.on("change", update_widget_state);
    }

    setTimeout(update_widget_state, 300);
});
