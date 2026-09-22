console.log("SMART WORKFLOW WIDGET SCRIPT LOADED");

$(document).ready(function () {
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
    let seaOverlayLayer = null;
    let currentAnimationId = null;

    // Intercept Leaflet popup close button clicks globally to prevent Frappe router hijacking (#close)
    $(document).on('click', '.leaflet-popup-close-button', function (e) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        if (shipmentMap) {
            shipmentMap.closePopup();
        }
        return false;
    });

    // Professional SVG Vehicle Icons (Top-down AIS & FlightRadar24 Silhouettes)
    function get_vehicle_svg(method) {
        if (method === 'Air') {
            return `
                <svg width="24" height="24" viewBox="0 0 24 24" fill="#007AFF" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 1.5C11.2 1.5 10.6 2.3 10.6 3.2V8.8L2.4 13.5C1.8 13.8 1.5 14.5 1.5 15.1C1.5 15.9 2.2 16.5 3 16.5H10.6V20.2L8.2 21.8C7.9 22 7.7 22.3 7.7 22.7C7.7 23.4 8.3 24 9 24H15C15.7 24 16.3 23.4 16.3 22.7C16.3 22.3 16.1 22 15.8 21.8L13.4 20.2V16.5H21C21.8 16.5 22.5 15.9 22.5 15.1C22.5 14.5 22.2 13.8 21.6 13.5L13.4 8.8V3.2C13.4 2.3 12.8 1.5 12 1.5Z" stroke="#0047AB" stroke-width="0.5"/>
                </svg>
            `;
        } else if (method === 'Ocean') {
            return `
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 1 C14.8 3.5 18 8 18 14 V20 C18 21.7 16.7 23 15 23 H9 C7.3 23 6 21.7 6 20 V14 C6 8 9.2 3.5 12 1 Z" fill="#0055B3" stroke="#003380" stroke-width="0.8"/>
                    <rect x="8" y="6.5" width="8" height="2.2" rx="0.4" fill="#38BDF8"/>
                    <rect x="8" y="9.7" width="8" height="2.2" rx="0.4" fill="#BAE6FD"/>
                    <rect x="8" y="12.9" width="8" height="2.2" rx="0.4" fill="#38BDF8"/>
                    <rect x="8" y="16.1" width="8" height="2.2" rx="0.4" fill="#BAE6FD"/>
                    <rect x="8.5" y="19.2" width="7" height="2.6" rx="0.5" fill="#FFFFFF"/>
                    <rect x="10.5" y="20" width="3" height="1" fill="#0055B3"/>
                </svg>
            `;
        } else {
            return `
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="6" y="8.5" width="12" height="14" rx="1.2" fill="#EA580C" stroke="#C2410C" stroke-width="0.6"/>
                    <line x1="7.5" y1="11.5" x2="16.5" y2="11.5" stroke="#FFEDD5" stroke-width="0.8"/>
                    <line x1="7.5" y1="14.5" x2="16.5" y2="14.5" stroke="#FFEDD5" stroke-width="0.8"/>
                    <line x1="7.5" y1="17.5" x2="16.5" y2="17.5" stroke="#FFEDD5" stroke-width="0.8"/>
                    <line x1="7.5" y1="20.5" x2="16.5" y2="20.5" stroke="#FFEDD5" stroke-width="0.8"/>
                    <rect x="7" y="1.5" width="10" height="5.8" rx="1.5" fill="#C2410C"/>
                    <rect x="8.5" y="2.5" width="7" height="2" rx="0.5" fill="#FEF08A"/>
                    <rect x="5.2" y="3" width="1.5" height="1" rx="0.3" fill="#C2410C"/>
                    <rect x="17.3" y="3" width="1.5" height="1" rx="0.3" fill="#C2410C"/>
                </svg>
            `;
        }
    }

    // Professional Hub Icons (Seaport ⚓ / Airport 🛫)
    function get_hub_icon_svg(hubType) {
        if (hubType === 'Ocean' || hubType === 'seaport' || hubType === 'port') {
            return `
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#0055B3" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="5" r="3"/>
                    <line x1="12" y1="22" x2="12" y2="8"/>
                    <path d="M5 12H2a10 10 0 0 0 20 0h-3"/>
                </svg>
            `;
        } else {
            return `
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#007AFF" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.2-1.1.6L2.5 8l6.4 3.3L7 15l-3.3-1.1-1.2 1.3 4.2 3.8 3.8 4.2 1.3-1.2L10.7 18.7l3.7-1.9 3.3 6.4 1.2-1.2-.4-2.6Z"/>
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
            $('#lw-fab-main').on('click', function () {
                $(this).toggleClass('active');
                if ($(this).hasClass('active')) {
                    $('#lw-fab-menu').addClass('show');
                } else {
                    $('#lw-fab-menu').removeClass('show');
                    $('.lw-popup').hide();
                }
            });

            $('.lw-sub-fab').on('click', function () {
                let target = $(this).attr('id').replace('lw-fab-', 'lw-popup-');
                $('.lw-popup').hide();
                $('#' + target).show();

                if (target === 'lw-popup-shipment') {
                    open_shipment_view();
                }
            });

            $('.lw-popup-close').on('click', function () {
                $($(this).data('target')).hide();
                if (currentAnimationId) {
                    cancelAnimationFrame(currentAnimationId);
                    currentAnimationId = null;
                }
                if (shipmentMap) {
                    try { shipmentMap.remove(); } catch (e) { }
                    shipmentMap = null;
                    seaOverlayLayer = null;
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

    // List shipments with interactive Status Filter Combobox
    function show_active_shipments_list(selectedFilter = 'active') {
        let $content = $('#lw-shipment-content');

        let headerHtml = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; gap: 8px;">
                <div style="flex: 1; min-width: 0;">
                    <strong style="color: #1f272e; font-size: 13.5px;">Danh sách Lô hàng Quốc tế:</strong>
                    <div style="font-size: 11px; color: #6c757d; margin-top: 2px;">Nhấn vào đơn hàng để xem bản đồ lộ trình trực tiếp:</div>
                </div>
                <div style="flex-shrink: 0;">
                    <select id="lw-filter-status" class="form-control" style="font-size: 11.5px; height: 28px; border-radius: 6px; border: 1px solid #ced4da; background-color: #ffffff; padding: 1px 6px; cursor: pointer; min-width: 145px; font-weight: 500; color: #1f272e; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                        <option value="active" ${selectedFilter === 'active' ? 'selected' : ''}>🚚 Đang vận chuyển</option>
                        <option value="completed" ${selectedFilter === 'completed' ? 'selected' : ''}>✅ Đã hoàn thành</option>
                        <option value="customs" ${selectedFilter === 'customs' ? 'selected' : ''}>🏛️ Đang thông quan</option>
                        <option value="all" ${selectedFilter === 'all' ? 'selected' : ''}>🌐 Tất cả đơn hàng</option>
                    </select>
                </div>
            </div>
            <div id="lw-shipment-items-container">
                <div style="text-align: center; padding: 25px; color: #6c757d;">
                    <div class="spinner-border text-primary" role="status" style="width: 1.8rem; height: 1.8rem;"></div>
                    <div style="margin-top: 8px; font-size: 12px;">Đang tải danh sách lô hàng...</div>
                </div>
            </div>
        `;

        $content.html(headerHtml);

        $('#lw-filter-status').on('change', function () {
            let filterVal = $(this).val();
            fetch_and_render_shipments_items(filterVal);
        });

        fetch_and_render_shipments_items(selectedFilter);
    }

    function fetch_and_render_shipments_items(filterVal) {
        let $itemsContainer = $('#lw-shipment-items-container');
        $itemsContainer.html(`
            <div style="text-align: center; padding: 25px; color: #6c757d;">
                <div class="spinner-border text-primary" role="status" style="width: 1.8rem; height: 1.8rem;"></div>
                <div style="margin-top: 8px; font-size: 12px;">Đang lọc danh sách đơn hàng...</div>
            </div>
        `);

        frappe.call({
            method: 'logistics_wizard.api.get_active_shipments',
            args: { status_filter: filterVal },
            callback: function (r) {
                if (r.message && r.message.status === 'success') {
                    let pos = r.message.data || [];
                    if (pos.length === 0) {
                        let filterLabel = (filterVal === 'active') ? 'đang vận chuyển' : ((filterVal === 'completed') ? 'đã hoàn thành' : ((filterVal === 'customs') ? 'đang làm thủ tục thông quan' : ''));
                        $itemsContainer.html(`
                            <div style="text-align: center; padding: 35px 20px; color: #8d99a6;">
                                <div style="font-size: 32px; margin-bottom: 8px;">📦</div>
                                <strong>Không có đơn hàng nào ${filterLabel}.</strong>
                                <p style="font-size: 12px; margin-top: 6px;">Hãy thử chọn bộ lọc khác (ví dụ "Toàn bộ đơn hàng") để xem tất cả.</p>
                            </div>
                        `);
                        return;
                    }

                    let html = `<div class="lw-shipment-list" style="display: flex; flex-direction: column; gap: 8px;">`;

                    pos.forEach(p => {
                        let badgeBg = '#e7f1ff';
                        let badgeColor = '#007AFF';
                        let badgeIcon = '🚚';

                        if (p.is_completed || p.status === 'Completed') {
                            badgeBg = '#e6f4ea';
                            badgeColor = '#137333';
                            badgeIcon = '✅';
                        } else if (p.is_customs || p.status === 'Customs Clearance') {
                            badgeBg = '#fef7e0';
                            badgeColor = '#b06000';
                            badgeIcon = '🏛️';
                        } else if (p.status === 'Draft') {
                            badgeBg = '#f1f3f4';
                            badgeColor = '#5f6368';
                            badgeIcon = '📝';
                        }

                        let methodIcon = (p.shipping_method === 'Air') ? '✈️' : ((p.shipping_method === 'Ocean') ? '🚢' : '🚚');
                        let routeHint = (p.origin_port && p.destination_port) ? ` &bull; ${p.origin_port} → ${p.destination_port}` : '';

                        html += `
                            <div class="lw-shipment-item" data-name="${p.name}" style="padding: 12px 14px; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; cursor: pointer; transition: all 0.2s;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <strong style="color: #007AFF; font-size: 13px;">${p.name}</strong>
                                        <span style="font-size: 11px; color: #6c757d; margin-left: 6px;">${methodIcon}${routeHint}</span>
                                    </div>
                                    <span class="badge" style="background: ${badgeBg}; color: ${badgeColor}; font-weight: 500; font-size: 11px; padding: 4px 8px; border-radius: 4px;">
                                        ${badgeIcon} ${p.status}
                                    </span>
                                </div>
                                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #495057; margin-top: 5px;">
                                    <div><strong>Nhà cung cấp:</strong> ${p.supplier_name || 'N/A'}</div>
                                    ${p.shipment_tracking ? `<span style="color: #6c757d; font-size: 11px;">Vận đơn: <strong>${p.shipment_tracking}</strong></span>` : ''}
                                </div>
                            </div>
                        `;
                    });

                    html += `</div>`;
                    $itemsContainer.html(html);

                    $('.lw-shipment-item').hover(
                        function () { $(this).css({ 'background': '#eef5ff', 'border-color': '#b8d5fd' }); },
                        function () { $(this).css({ 'background': '#f8f9fa', 'border-color': '#e9ecef' }); }
                    ).on('click', function () {
                        let name = $(this).data('name');
                        load_shipment_map(name, 'Purchase Order');
                    });
                } else {
                    $itemsContainer.html('<div style="text-align: center; color: red; padding: 20px;">Lỗi tải danh sách vận chuyển.</div>');
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
                    <div id="lw-timeline-container" style="margin-top: 6px;"></div>
                </div>
            </div>
        `);

        $('#lw-btn-back-shipments').on('click', function () {
            if (currentAnimationId) {
                cancelAnimationFrame(currentAnimationId);
                currentAnimationId = null;
            }
            if (shipmentMap) {
                try { shipmentMap.remove(); } catch (e) { }
                shipmentMap = null;
                seaOverlayLayer = null;
            }
            show_active_shipments_list();
        });

        // Call backend API
        frappe.call({
            method: 'logistics_wizard.api.get_shipment_tracking',
            args: { docname: docname, doctype: doctype },
            callback: function (r) {
                if (r.message && r.message.status === 'success') {
                    init_map(r.message.data, docname, doctype);
                } else {
                    $('#lw-map-info-text').html(`<span style="color: #d9534f;">${r.message ? r.message.message : "Không thể tải thông tin lộ trình."}</span>`);
                }
            }
        });
    }

    // --------------------------------------------------------------------------
    // High-Performance Map Utilities (Douglas-Peucker, Bearing, Interpolation)
    // --------------------------------------------------------------------------

    /**
     * Dynamically toggles OpenSeaMap seamark navigation overlay based on shipping method.
     */
    function update_marine_overlay(method) {
        const Leaflet = window.L || window.leaflet;
        if (!Leaflet || !shipmentMap) return;

        const isOcean = (method === 'Ocean' || method === 'Sea');
        if (isOcean) {
            if (!seaOverlayLayer) {
                seaOverlayLayer = Leaflet.tileLayer('https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png', {
                    attribution: 'Map data: &copy; <a href="http://www.openseamap.org">OpenSeaMap</a> contributors',
                    maxZoom: 18,
                    opacity: 1.0
                });
            }
            if (!shipmentMap.hasLayer(seaOverlayLayer)) {
                seaOverlayLayer.addTo(shipmentMap);
            }
        } else {
            if (seaOverlayLayer && shipmentMap.hasLayer(seaOverlayLayer)) {
                shipmentMap.removeLayer(seaOverlayLayer);
            }
        }
    }

    /**
     * Perpendicular distance between point P and line segment (P1 - P2).
     * Handles International Date Line antimeridian wrap when |lon2 - lon1| > 180°.
     */
    function perpendicularDistance(p, p1, p2) {
        let [lat, lon] = p;
        let [lat1, lon1] = p1;
        let [lat2, lon2] = p2;

        let dLon = lon2 - lon1;
        let dLat = lat2 - lat1;

        // Normalize longitude wrap across Date Line
        if (dLon > 180) dLon -= 360;
        if (dLon < -180) dLon += 360;

        let pLon = lon - lon1;
        let pLat = lat - lat1;
        if (pLon > 180) pLon -= 360;
        if (pLon < -180) pLon += 360;

        let lenSq = dLon * dLon + dLat * dLat;
        if (lenSq === 0) {
            return Math.hypot(pLon, pLat);
        }

        let t = Math.max(0, Math.min(1, (pLon * dLon + pLat * dLat) / lenSq));
        let projLon = t * dLon;
        let projLat = t * dLat;

        return Math.hypot(pLon - projLon, pLat - projLat);
    }

    /**
     * Douglas-Peucker polyline simplification algorithm in pure JavaScript.
     * Preserves critical strait navigation while drastically reducing SVG/Canvas vertices.
     * @param {Array<[number, number]>} points - Array of [lat, lon]
     * @param {number} tolerance - Epsilon threshold in degrees (~0.002° ≈ 200m)
     */
    function douglasPeucker(points, tolerance = 0.002) {
        if (!points || !Array.isArray(points) || points.length <= 2) return points || [];

        let maxDist = 0;
        let maxIndex = 0;
        const end = points.length - 1;

        for (let i = 1; i < end; i++) {
            let dist = perpendicularDistance(points[i], points[0], points[end]);
            if (dist > maxDist) {
                maxDist = dist;
                maxIndex = i;
            }
        }

        if (maxDist > tolerance) {
            let left = douglasPeucker(points.slice(0, maxIndex + 1), tolerance);
            let right = douglasPeucker(points.slice(maxIndex), tolerance);
            return left.slice(0, left.length - 1).concat(right);
        } else {
            return [points[0], points[end]];
        }
    }

    /**
     * Computes initial Great-Circle bearing angle from point 1 to point 2 (degrees 0..360).
     * theta = atan2(y, x)
     */
    function calculateBearing(lat1, lon1, lat2, lon2) {
        const toRad = Math.PI / 180;
        const toDeg = 180 / Math.PI;
        const phi1 = lat1 * toRad;
        const phi2 = lat2 * toRad;
        let deltaLambda = (lon2 - lon1) * toRad;

        while (deltaLambda > Math.PI) deltaLambda -= 2 * Math.PI;
        while (deltaLambda < -Math.PI) deltaLambda += 2 * Math.PI;

        const y = Math.sin(deltaLambda) * Math.cos(phi2);
        const x = Math.cos(phi1) * Math.sin(phi2) - Math.sin(phi1) * Math.cos(phi2) * Math.cos(deltaLambda);
        const theta = Math.atan2(y, x);
        return (theta * toDeg + 360) % 360;
    }

    /**
     * Precalculates cumulative polyline distances along coordinate track.
     */
    function computePolylineMetrics(coords) {
        const cumulative = [0];
        let total = 0;
        if (!coords || coords.length <= 1) {
            return { cumulative: [0], total: 0 };
        }
        for (let i = 0; i < coords.length - 1; i++) {
            let [y1, x1] = coords[i];
            let [y2, x2] = coords[i + 1];
            let dx = x2 - x1;
            if (dx > 180) dx -= 360;
            if (dx < -180) dx += 360;
            let dy = y2 - y1;
            let cosLat = Math.cos(((y1 + y2) / 2) * Math.PI / 180);
            let dist = Math.hypot(dy, dx * cosLat);
            total += dist;
            cumulative.push(total);
        }
        return { cumulative, total };
    }

    /**
     * Continuously interpolates latitude, longitude, and bearing at progress ratio (0.0 .. 1.0).
     */
    function interpolateAtProgress(coords, metrics, progress) {
        if (!coords || coords.length === 0) return { point: [0, 0], bearing: 0 };
        if (coords.length === 1) return { point: coords[0], bearing: 0 };

        const p = Math.max(0, Math.min(1, progress));
        if (metrics.total === 0) return { point: coords[0], bearing: 0 };

        const targetDist = p * metrics.total;

        let segmentIdx = 0;
        for (let i = 0; i < metrics.cumulative.length - 1; i++) {
            if (targetDist >= metrics.cumulative[i] && targetDist <= metrics.cumulative[i + 1]) {
                segmentIdx = i;
                break;
            }
        }
        if (segmentIdx >= coords.length - 1) {
            segmentIdx = coords.length - 2;
        }

        const segStartDist = metrics.cumulative[segmentIdx];
        const segLen = metrics.cumulative[segmentIdx + 1] - segStartDist;
        const t = (segLen === 0) ? 0 : Math.max(0, Math.min(1, (targetDist - segStartDist) / segLen));

        const p1 = coords[segmentIdx];
        const p2 = coords[segmentIdx + 1] || p1;

        let lat = p1[0] + t * (p2[0] - p1[0]);
        let lon1 = p1[1];
        let lon2 = p2[1];
        let dLon = lon2 - lon1;
        if (dLon > 180) dLon -= 360;
        if (dLon < -180) dLon += 360;
        let lon = lon1 + t * dLon;

        const bearing = calculateBearing(p1[0], p1[1], p2[0], p2[1]);
        return { point: [lat, lon], bearing };
    }

    /**
     * Animates vehicle marker smoothly along polyline using requestAnimationFrame with cubic ease-out.
     * Features dynamic vehicle morphing (Truck 🚚 -> Ship 🚢 / Plane ✈️ -> Truck 🚚)
     * based on multimodal progress thresholds and real-time tangent bearing rotation.
     */
    function animateVehicle(marker, coords, targetProgress, durationMs = 1500, legs = [], thresholds = [0, 0.05, 0.95, 1], mainMethod = 'Ocean', trackingData = null) {
        if (currentAnimationId) {
            cancelAnimationFrame(currentAnimationId);
            currentAnimationId = null;
        }

        if (!marker || !coords || coords.length === 0) return;

        const metrics = computePolylineMetrics(coords);
        const startProgress = (typeof marker._currentProgress === 'number') ? marker._currentProgress : 0;
        const clampedTarget = Math.max(0, Math.min(1, targetProgress));
        const startTime = performance.now();

        const p1 = (thresholds && thresholds.length > 1) ? thresholds[1] : 0.05;
        const p2 = (thresholds && thresholds.length > 2) ? thresholds[2] : 0.95;

        function frame(now) {
            const elapsed = now - startTime;
            const rawT = durationMs <= 0 ? 1 : Math.min(1, elapsed / durationMs);
            // Cubic ease-out: 1 - (1 - t)^3
            const easeT = 1 - Math.pow(1 - rawT, 3);
            const curP = startProgress + (clampedTarget - startProgress) * easeT;

            const { point, bearing } = interpolateAtProgress(coords, metrics, curP);
            marker.setLatLng(point);

            // Determine active mode and styling for dynamic vehicle morphing
            let activeMode = 'Road';
            let activeDesc = 'Chặng 1: Vận chuyển đường bộ (First-mile Road)';
            let borderColor = '#FF9500';

            const isNearArrivalHub = Math.abs(curP - p2) <= 0.015 || (curP >= p2 && Math.abs(clampedTarget - p2) <= 0.02);

            if (curP <= p1) {
                activeMode = 'Road';
                activeDesc = 'Chặng 1: Xe tải container vận chuyển ra Cảng/Sân bay xuất phát';
                borderColor = '#FF9500';
            } else if (isNearArrivalHub) {
                activeMode = mainMethod;
                let hubName = (trackingData && trackingData.arrival_hub && trackingData.arrival_hub.name)
                    ? trackingData.arrival_hub.name
                    : 'Cảng/Sân bay đến';
                activeDesc = 'Đã cập bến và đang làm thủ tục thông quan hải quan tại ' + hubName;
                borderColor = '#28a745';
            } else if (curP < p2) {
                activeMode = mainMethod;
                activeDesc = (mainMethod === 'Air')
                    ? 'Chặng 2: Máy bay vận tải đang bay qua không phận Quốc tế (Air Transit)'
                    : 'Chặng 2: Tàu container đang vượt hải trình Thái Bình Dương (Ocean Transit)';
                borderColor = (mainMethod === 'Air') ? '#007AFF' : '#0055B3';
            } else {
                activeMode = 'Road';
                let targetDestName = (trackingData && trackingData.destination && trackingData.destination.name)
                    ? trackingData.destination.name
                    : 'Kho đích nhận hàng';
                activeDesc = 'Chặng 3: Xe tải container giao nhận về ' + targetDestName + ' (Last-mile Road)';
                borderColor = '#FF9500';
            }

            const iconEl = marker.getElement ? marker.getElement() : null;
            if (iconEl) {
                // Morph vehicle icon if mode changes
                if (marker._activeMode !== activeMode) {
                    marker._activeMode = activeMode;
                    const boxEl = iconEl.querySelector('.lw-vehicle-box');
                    if (boxEl) {
                        boxEl.style.borderColor = borderColor;
                    }
                    const svgEl = iconEl.querySelector('.lw-vehicle-icon-svg');
                    if (svgEl) {
                        svgEl.innerHTML = get_vehicle_svg(activeMode);
                    }
                }

                // Update heading orientation with bearing rotation
                const rotEl = iconEl.querySelector('.lw-vehicle-icon-svg') || iconEl.querySelector('svg');
                if (rotEl) {
                    rotEl.style.transform = `rotate(${bearing}deg)`;
                    rotEl.style.transformOrigin = 'center center';
                }
            }

            marker._currentProgress = curP;

            if (rawT < 1) {
                currentAnimationId = requestAnimationFrame(frame);
            } else {
                currentAnimationId = null;

                // Precision Milestone Snap: Snap exactly to anchor coordinates when vehicle arrives at station
                if (clampedTarget <= 0.001) {
                    marker.setLatLng(coords[0]);
                } else if (Math.abs(clampedTarget - p2) <= 0.02) {
                    let snapCoord = (trackingData && trackingData._ahCoord) ? trackingData._ahCoord : null;
                    if (!snapCoord && trackingData && trackingData.arrival_hub && trackingData.arrival_hub.coordinates) {
                        snapCoord = [
                            trackingData.arrival_hub.coordinates[0],
                            alignLongitude(trackingData.arrival_hub.coordinates[1], coords[coords.length - 1][1])
                        ];
                    }
                    if (snapCoord) {
                        marker.setLatLng([snapCoord[0], snapCoord[1]]);
                    }
                } else if (clampedTarget >= 0.999) {
                    marker.setLatLng(coords[coords.length - 1]);
                }

                // Fix progress text in popup content on animation completion
                if (marker.getPopup && marker.getPopup()) {
                    const finalVehName = (activeMode === 'Ocean') ? 'Tàu biển 🚢' : ((activeMode === 'Air') ? 'Máy bay ✈️' : 'Xe tải Container 🚚');
                    marker.setPopupContent(`<b>Phương tiện: ${finalVehName}</b><br>${activeDesc}<br><small>Tiến trình toàn trình: ${(clampedTarget * 100).toFixed(1)}%</small>`);
                }
            }
        }

        currentAnimationId = requestAnimationFrame(frame);
    }

    /**
     * Aligns target longitude to reference longitude to prevent 360-degree antimeridian jumps.
     */
    function alignLongitude(lon, refLon) {
        if (typeof lon !== 'number' || typeof refLon !== 'number') return lon;
        let adjusted = lon;
        while (adjusted - refLon > 180) adjusted -= 360;
        while (adjusted - refLon < -180) adjusted += 360;
        return adjusted;
    }

    // Initialize Leaflet Map
    function init_map(data, docname, doctype) {
        const Leaflet = window.L || window.leaflet;
        if (!Leaflet) {
            $('#lw-map-info-text').html('<span style="color: red;">Thư viện bản đồ (Leaflet) chưa được tải.</span>');
            return;
        }

        if (currentAnimationId) {
            cancelAnimationFrame(currentAnimationId);
            currentAnimationId = null;
        }

        if (shipmentMap) {
            try { shipmentMap.remove(); } catch (e) { }
            shipmentMap = null;
            seaOverlayLayer = null;
        }

        // Clean slate
        mapMarkers = [];
        mapPolyline = null;

        // Create Map
        shipmentMap = Leaflet.map('shipment-map', {
            zoomControl: true,
            attributionControl: true
        }).setView([20.0, 150.0], 3);
        window._lw_shipment_map = shipmentMap;

        // Sanitize close buttons on any popup opened on this map to prevent #close routing error
        shipmentMap.on('popupopen', function (e) {
            if (e && e.popup && e.popup._container) {
                $(e.popup._container).find('.leaflet-popup-close-button').each(function () {
                    $(this).attr('href', 'javascript:void(0);')
                        .attr('role', 'button')
                        .on('click', function (ev) {
                            ev.preventDefault();
                            ev.stopPropagation();
                            ev.stopImmediatePropagation();
                            if (shipmentMap) shipmentMap.closePopup();
                            return false;
                        });
                });
            }
        });

        // 1. OpenStreetMap Standard basemap (Free, No watermark, Max Zoom 19)
        Leaflet.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            subdomains: ['a', 'b', 'c'],
            maxZoom: 19
        }).addTo(shipmentMap);

        // 2. OpenSeaMap Marine Overlay (dynamic toggle for Ocean/Sea)
        update_marine_overlay(data.method);

        let fullRoute = (data.full_route && data.full_route.length > 0) ? data.full_route : (data.route || []);
        if (!fullRoute || fullRoute.length === 0) {
            $('#lw-map-info-text').html('<span class="text-muted">Chưa có tọa độ nào được ghi nhận cho đơn hàng này.</span>');
            return;
        }

        // 3. Douglas-Peucker Polyline Simplification for entire route
        let simplifiedCoords = douglasPeucker(fullRoute, 0.002);
        if (!simplifiedCoords || simplifiedCoords.length < 2) {
            simplifiedCoords = fullRoute;
        }

        // 4. Render Multi-leg Polylines (Dashed orange for road, solid blue for ocean/air)
        let polylineLayers = [];
        if (data.legs && Array.isArray(data.legs) && data.legs.length > 0) {
            data.legs.forEach(leg => {
                let legRaw = leg.coordinates_latlon || [];
                if (legRaw.length >= 2) {
                    let legSimp = douglasPeucker(legRaw, 0.002);
                    if (!legSimp || legSimp.length < 2) legSimp = legRaw;

                    let isRoad = (leg.mode === 'Road');
                    let isAir = (leg.mode === 'Air');
                    let legColor = isRoad ? '#FF9500' : (isAir ? '#007AFF' : '#0055B3');
                    let legDash = isRoad ? '6, 8' : '';
                    let legWeight = isRoad ? 3.5 : 4.0;

                    let pLayer = Leaflet.polyline(legSimp, {
                        color: legColor,
                        weight: legWeight,
                        opacity: 0.92,
                        dashArray: legDash
                    }).addTo(shipmentMap);
                    polylineLayers.push(pLayer);
                }
            });
        }

        // Fallback single polyline if no legs rendered
        if (polylineLayers.length === 0) {
            let singleLine = Leaflet.polyline(simplifiedCoords, {
                color: data.method === 'Air' ? '#007AFF' : (data.method === 'Ocean' ? '#0055B3' : '#FF9500'),
                weight: 3.5,
                opacity: 0.9,
                dashArray: data.method === 'Road' ? '6, 8' : ''
            }).addTo(shipmentMap);
            polylineLayers.push(singleLine);
        }

        // Fit map bounds across all polylines
        try {
            let group = Leaflet.featureGroup(polylineLayers);
            shipmentMap.fitBounds(group.getBounds(), { padding: [40, 40], maxZoom: 8 });
        } catch (e) { }

        // 5. Origin Marker O (Origin - Kho nguồn, Green Badge)
        let originCoord = simplifiedCoords[0];
        let originName = (data.origin && data.origin.name) || (typeof data.origin === 'string' ? data.origin : 'Kho nhà máy xuất phát');
        let originIcon = Leaflet.divIcon({
            className: 'custom-origin-icon',
            html: `<div style="background: #28a745; color: white; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 800; border: 2.5px solid white; box-shadow: 0 3px 8px rgba(0,0,0,0.35); cursor: pointer;" title="Điểm xuất phát (Origin - Điểm O)">O</div>`,
            iconSize: [28, 28],
            iconAnchor: [14, 14]
        });
        let origMarker = Leaflet.marker(originCoord, { icon: originIcon }).addTo(shipmentMap);
        origMarker.bindPopup(`<b>Kho xuất phát (Origin - Điểm O):</b><br>${originName}<br><small>Toạ độ: ${originCoord[0].toFixed(4)}, ${originCoord[1].toFixed(4)}</small>`);
        mapMarkers.push(origMarker);

        // 6. Destination Marker D (Destination - Kho đích nhận hàng, Red Badge)
        let destCoord = simplifiedCoords[simplifiedCoords.length - 1];
        let destName = (data.destination && data.destination.name) || (typeof data.destination === 'string' ? data.destination : 'Kho đích nhận hàng');
        let destIcon = Leaflet.divIcon({
            className: 'custom-dest-icon',
            html: `<div style="background: #dc3545; color: white; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 800; border: 2.5px solid white; box-shadow: 0 3px 8px rgba(0,0,0,0.35); cursor: pointer;" title="Điểm đích đến (Destination - Điểm D)">D</div>`,
            iconSize: [28, 28],
            iconAnchor: [14, 14]
        });
        let dstMarker = Leaflet.marker(destCoord, { icon: destIcon }).addTo(shipmentMap);
        let dispDestLon = ((destCoord[1] + 180) % 360 + 360) % 360 - 180;
        dstMarker.bindPopup(`<b>Kho đích nhận hàng (Destination - Điểm D):</b><br>${destName}<br><small>Toạ độ: ${destCoord[0].toFixed(4)}, ${dispDestLon.toFixed(4)}</small>`);
        mapMarkers.push(dstMarker);

        // 7. Intermediary Hub Markers (Departure Hub & Arrival Hub: ⚓ / 🛫)
        let dhCoord = null;
        if (data.legs && data.legs.length >= 1 && data.legs[0].coordinates_latlon && data.legs[0].coordinates_latlon.length > 0) {
            const leg1Coords = data.legs[0].coordinates_latlon;
            dhCoord = leg1Coords[leg1Coords.length - 1];
        } else if (data.departure_hub && data.departure_hub.coordinates) {
            dhCoord = [
                data.departure_hub.coordinates[0],
                alignLongitude(data.departure_hub.coordinates[1], originCoord[1])
            ];
        }

        if (dhCoord && data.departure_hub) {
            let dhIcon = Leaflet.divIcon({
                className: 'custom-dep-hub-icon',
                html: `<div style="background: white; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; border: 2.5px solid ${data.method === 'Air' ? '#007AFF' : '#0055B3'}; box-shadow: 0 2px 6px rgba(0,0,0,0.25); cursor: pointer;" title="Trạm trung chuyển xuất phát">
                    ${get_hub_icon_svg(data.method)}
                </div>`,
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            });
            let dhMarker = Leaflet.marker([dhCoord[0], dhCoord[1]], { icon: dhIcon }).addTo(shipmentMap);
            let dispDhLon = ((dhCoord[1] + 180) % 360 + 360) % 360 - 180;
            dhMarker.bindPopup(`<b>Trạm trung chuyển xuất phát:</b><br>${data.departure_hub.name || 'Cảng/Sân bay xuất'}<br><small>Toạ độ: ${dhCoord[0].toFixed(4)}, ${dispDhLon.toFixed(4)}</small>`);
            mapMarkers.push(dhMarker);
        }

        let ahCoord = null;
        if (data.legs && data.legs.length >= 2 && data.legs[1].coordinates_latlon && data.legs[1].coordinates_latlon.length > 0) {
            const leg2Coords = data.legs[1].coordinates_latlon;
            ahCoord = leg2Coords[leg2Coords.length - 1];
        } else if (data.arrival_hub && data.arrival_hub.coordinates) {
            ahCoord = [
                data.arrival_hub.coordinates[0],
                alignLongitude(data.arrival_hub.coordinates[1], destCoord[1])
            ];
        }

        if (ahCoord && data.arrival_hub) {
            let ahIcon = Leaflet.divIcon({
                className: 'custom-arr-hub-icon',
                html: `<div style="background: white; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; border: 2.5px solid ${data.method === 'Air' ? '#007AFF' : '#0055B3'}; box-shadow: 0 2px 6px rgba(0,0,0,0.25); cursor: pointer;" title="Trạm trung chuyển đến">
                    ${get_hub_icon_svg(data.method)}
                </div>`,
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            });
            let ahMarker = Leaflet.marker([ahCoord[0], ahCoord[1]], { icon: ahIcon }).addTo(shipmentMap);
            let dispAhLon = ((ahCoord[1] + 180) % 360 + 360) % 360 - 180;
            ahMarker.bindPopup(`<b>Trạm trung chuyển đến:</b><br>${data.arrival_hub.name || 'Cảng/Sân bay đến'}<br><small>Toạ độ: ${ahCoord[0].toFixed(4)}, ${dispAhLon.toFixed(4)}</small>`);
            mapMarkers.push(ahMarker);
        }

        // Store aligned hub coordinates inside tracking data for animation milestone snaps
        data._dhCoord = dhCoord;
        data._ahCoord = ahCoord;

        // 8. Vehicle Marker with Dynamic Morphing & requestAnimationFrame Animation
        let targetProgress = (typeof data.progress === 'number') ? data.progress : 0.55;
        let thresholds = data.progress_thresholds || [0, 0.05, 0.95, 1];
        let initMode = 'Road';
        if (targetProgress > thresholds[1] && targetProgress <= thresholds[2]) {
            initMode = data.method;
        }
        let initBorderColor = (initMode === 'Road') ? '#FF9500' : (data.method === 'Air' ? '#007AFF' : '#0055B3');

        let routeMetrics = computePolylineMetrics(simplifiedCoords);
        let startPosData = interpolateAtProgress(simplifiedCoords, routeMetrics, 0);

        let vehicleIcon = Leaflet.divIcon({
            className: 'custom-vehicle-icon',
            html: `
                <div class="lw-vehicle-box" style="background: white; border-radius: 50%; width: 42px; height: 42px; display: flex; align-items: center; justify-content: center; box-shadow: 0 3px 10px rgba(0,0,0,0.3); border: 2.8px solid ${initBorderColor}; transition: border-color 0.3s;">
                    <div class="lw-vehicle-icon-svg" style="display: flex; align-items: center; justify-content: center; transform: rotate(${startPosData.bearing}deg); transform-origin: center center;">
                        ${get_vehicle_svg(initMode)}
                    </div>
                </div>
            `,
            iconSize: [42, 42],
            iconAnchor: [21, 21]
        });

        let vehMarker = Leaflet.marker(startPosData.point, { icon: vehicleIcon, zIndexOffset: 1000 }).addTo(shipmentMap);
        vehMarker._currentProgress = 0;
        vehMarker._activeMode = initMode;
        vehMarker.bindPopup(`<b>Vị trí phương tiện:</b><br>${data.current_location || 'Đang vận chuyển'}`);
        mapMarkers.push(vehMarker);

        // Trigger smooth vehicle animation with dynamic morphing (~1.6s)
        animateVehicle(vehMarker, simplifiedCoords, targetProgress, 1600, data.legs || [], thresholds, data.method, data);

        setTimeout(() => {
            if (vehMarker && shipmentMap && shipmentMap.hasLayer(vehMarker)) {
                vehMarker.openPopup();
            }
        }, 1650);

        // 9. Update Info Card with Balanced 2-Tier Layout (Status Banner + 50/50 Dual Columns)
        let methodIconText = (data.method === 'Air')
            ? '✈️ Đa phương thức Hàng không (Air)'
            : ((data.method === 'Ocean') ? '🚢 Đa phương thức Đường biển (Ocean)' : '🚚 Đường bộ nội địa (Road)');

        let statusBg = '#e0f2fe';
        let statusColor = '#0369a1';
        let statusIcon = '🚢';

        if (data.progress >= 1.0 || (data.status_text && (data.status_text.includes('giao hàng thành công') || data.status_text.includes('Hoàn thành')))) {
            statusBg = '#dcfce7';
            statusColor = '#15803d';
            statusIcon = '✅';
        } else if (data.status_text && (data.status_text.includes('thông quan') || data.status_text.includes('Hải quan') || data.status_text.includes('Customs'))) {
            statusBg = '#fef3c7';
            statusColor = '#b45309';
            statusIcon = '🏛️';
        } else if (data.method === 'Air') {
            statusIcon = '✈️';
        }

        let infoHtml = `
            <div style="display: flex; flex-direction: column; gap: 8px;">
                <!-- Tầng 1: Banner Trạng thái vận hành -->
                <div style="display: flex; justify-content: space-between; align-items: center; background: #ffffff; padding: 7px 12px; border-radius: 6px; border: 1px solid #e2e8f0; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                    <span style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px; color: #64748b;">Trạng thái vận hành</span>
                    <span class="badge" style="background: ${statusBg}; color: ${statusColor}; font-size: 11.5px; font-weight: 600; padding: 4px 10px; border-radius: 10px; white-space: normal; text-align: right; line-height: 1.3; max-width: 72%;">
                        ${statusIcon} ${data.status_text}
                    </span>
                </div>

                <!-- Tầng 2: 2 Khối 50-50 Cân xứng -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div style="background: #ffffff; padding: 9px 12px; border-radius: 6px; border: 1px solid #e2e8f0; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                        <div>
                            <div style="font-size: 10.5px; color: #64748b; font-weight: 600; text-transform: uppercase; margin-bottom: 2px;">Mô hình vận tải</div>
                            <div style="font-size: 12px; font-weight: 600; color: #0f172a; line-height: 1.3;">${methodIconText}</div>
                        </div>
                        <div style="font-size: 11.5px; color: #0284c7; font-weight: 600; margin-top: 4px;">
                            Cự ly: ${Math.round(data.distance_km || 0).toLocaleString()} km
                        </div>
                    </div>

                    <div style="background: #ffffff; padding: 9px 12px; border-radius: 6px; border: 1px solid #e2e8f0; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                        <div>
                            <div style="font-size: 10.5px; color: #64748b; font-weight: 600; text-transform: uppercase; margin-bottom: 2px;">Vị trí hiện tại</div>
                            <div style="font-size: 12px; font-weight: 600; color: #0284c7; line-height: 1.3; word-break: break-word;" title="${data.current_location}">
                                📍 ${data.current_location}
                            </div>
                        </div>
                        <div style="font-size: 11px; color: #64748b; margin-top: 4px;">
                            Tiến trình: <strong style="color: #0284c7;">${Math.round((data.progress || 0) * 100)}%</strong>
                        </div>
                    </div>
                </div>
            </div>
        `;
        $('#lw-map-info-text').html(infoHtml);

        // 10. Render Checkpoints in Timeline
        render_checkpoints_timeline(docname, doctype, data);

        // Invalidate map size after animation/popup display
        setTimeout(() => {
            if (shipmentMap) {
                shipmentMap.invalidateSize();
            }
        }, 300);
    }

    // Render Timeline below the map
    function render_checkpoints_timeline(docname, doctype, data) {
        let $timeline = $('#lw-timeline-container');

        // Priority 1: Use enriched checkpoints directly from get_shipment_tracking API data
        if (data && data.checkpoints && data.checkpoints.length > 0) {
            draw_timeline_items(data.checkpoints, $timeline, data);
            return;
        }

        // Priority 2: If window.cur_frm is this document and has transit_route
        if (window.cur_frm && cur_frm.doc && (cur_frm.doc.name === docname) && cur_frm.doc.transit_route && cur_frm.doc.transit_route.length > 0) {
            draw_timeline_items(cur_frm.doc.transit_route, $timeline, data);
            return;
        }

        // Priority 3: Otherwise fetch via frappe.db.get_doc
        let targetDocType = doctype;
        let targetDocName = docname;

        if (doctype === 'Purchase Order') {
            frappe.db.get_value('Shipment Tracking', { purchase_order: docname }, 'name').then(r => {
                if (r && r.message && r.message.name) {
                    frappe.db.get_doc('Shipment Tracking', r.message.name).then(doc => {
                        draw_timeline_items(doc.transit_route || [], $timeline, data);
                    });
                } else {
                    $timeline.html('<div style="color: #8d99a6; font-size: 12px; padding: 8px 0;">Chưa liên kết phiếu Shipment Tracking hoặc chưa có lộ trình chi tiết.</div>');
                }
            });
        } else if (doctype === 'Shipment Tracking') {
            frappe.db.get_doc('Shipment Tracking', docname).then(doc => {
                draw_timeline_items(doc.transit_route || [], $timeline, data);
            });
        } else {
            $timeline.html('<div style="color: #8d99a6; font-size: 12px; padding: 8px 0;">Không có dữ liệu lộ trình.</div>');
        }
    }

    function draw_timeline_items(routes, $container, data) {
        if (!routes || routes.length === 0) {
            $container.html('<div style="color: #8d99a6; font-size: 12px; padding: 8px 0;">Chưa có trạm lộ trình nào.</div>');
            return;
        }

        let hasExplicitCurrent = routes.some(r => r.is_current === true || (r.activity && r.activity.includes('(Current Position)')));

        let html = '<div class="lw-timeline">';
        routes.forEach((r, idx) => {
            let isLast = (idx === routes.length - 1);
            let isCurrent = (r.is_current === true) || (r.activity && r.activity.includes('(Current Position)')) || (!hasExplicitCurrent && isLast);
            let cleanActivity = (r.activity || '').replace(' (Current Position)', '').replace('(Current Position)', '').trim();

            let itemClass = isCurrent ? 'lw-timeline-item current-step' : 'lw-timeline-item completed';
            let badgeHtml = isCurrent
                ? `<span class="lw-timeline-current-badge">📍 Vị trí hiện tại</span>`
                : '';

            html += `
                <div class="${itemClass}">
                    <div class="lw-timeline-node"></div>
                    <div class="lw-timeline-date">${r.date || ''}</div>
                    <div class="lw-timeline-title">
                        <span>${cleanActivity}</span>
                        ${badgeHtml}
                    </div>
                    <div class="lw-timeline-desc">📍 ${r.location || ''}</div>
                    ${r.notes ? `<div class="lw-timeline-notes">${r.notes}</div>` : ''}
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
                callback: function (r) {
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

    // Expose Map API for automated verification & programmatic control
    window.LogisticsWizardMap = {
        douglasPeucker: douglasPeucker,
        perpendicularDistance: perpendicularDistance,
        calculateBearing: calculateBearing,
        computePolylineMetrics: computePolylineMetrics,
        interpolateAtProgress: interpolateAtProgress,
        animateVehicle: animateVehicle,
        update_marine_overlay: update_marine_overlay,
        getShipmentMap: function () { return shipmentMap; },
        getSeaOverlayLayer: function () { return seaOverlayLayer; },
        getMapPolyline: function () { return mapPolyline; },
        getMapMarkers: function () { return mapMarkers; }
    };

    setTimeout(update_widget_state, 300);
});

