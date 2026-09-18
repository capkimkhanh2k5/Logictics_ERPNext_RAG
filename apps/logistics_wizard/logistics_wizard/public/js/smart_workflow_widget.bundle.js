console.log("SMART WORKFLOW WIDGET SCRIPT LOADED"); $(document).ready(function() {
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

    // Inject FAB and Modals
    function inject_fab() {
        if ($('#lw-fab-container').length === 0) {
            let fab_html = `
                <div id="lw-fab-container">
                    <button class="lw-fab" id="lw-fab-main">📦</button>
                    <div id="lw-fab-menu">
                        <button class="lw-fab lw-sub-fab" id="lw-fab-workflow" data-tooltip="Tiến trình (Workflow)">📋</button>
                        <button class="lw-fab lw-sub-fab" id="lw-fab-shipment" data-tooltip="Hành trình (Shipment)">🚚</button>
                        <button class="lw-fab lw-sub-fab" id="lw-fab-ai" data-tooltip="AI Chat">🤖</button>
                    </div>
                </div>

                <!-- Popup: Workflow -->
                <div class="lw-popup" id="lw-popup-workflow">
                    <div class="lw-popup-header">
                        Tiến trình chứng từ
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

                <!-- Popup: Shipment -->
                <div class="lw-popup" id="lw-popup-shipment">
                    <div class="lw-popup-header">
                        Hành trình Giao hàng
                        <span class="lw-popup-close" data-target="#lw-popup-shipment">✖</span>
                    </div>
                    <div class="lw-popup-body" id="lw-shipment-content">
                        <div style="text-align: center; color: #8d99a6; padding: 20px 0;">
                            Vui lòng mở một mã Theo dõi hành trình (Shipment Tracking) để xem lộ trình chi tiết.
                        </div>
                    </div>
                </div>

                <!-- Popup: AI Chat -->
                <div class="lw-popup" id="lw-popup-ai">
                    <div class="lw-popup-header">
                        Trợ lý AI Logistics
                        <span class="lw-popup-close" data-target="#lw-popup-ai">✖</span>
                    </div>
                    <div class="lw-popup-body" style="text-align: center; padding: 30px 15px;">
                        <div style="font-size: 40px; margin-bottom: 15px;">🚧</div>
                        <h4 style="margin:0 0 10px 0; color: #1f272e;">Tính năng đang phát triển</h4>
                        <p style="color: #8d99a6; margin: 0;">Trợ lý AI đang được huấn luyện nghiệp vụ và sẽ sớm ra mắt trong thời gian tới!</p>
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
                    $('.lw-popup').hide(); // Hide all popups when closing menu
                }
            });

            $('.lw-sub-fab').on('click', function() {
                let target = $(this).attr('id').replace('lw-fab-', 'lw-popup-');
                $('.lw-popup').hide(); // Hide others
                $('#' + target).show();
                
                // If shipment, load timeline if on Shipment Tracking
                if (target === 'lw-popup-shipment') {
                    render_shipment_timeline();
                }
            });

            $('.lw-popup-close').on('click', function() {
                $($(this).data('target')).hide();
            });
        }
    }

    // Render Shipment Timeline (Mock/Fetch data based on current page)
    function render_shipment_timeline() {
        let route = frappe.get_route();
        let $content = $('#lw-shipment-content');
        
        if (route && route[0] === 'Form' && route[1] === 'Shipment Tracking' && route[2]) {
            // Check if frm is available to read transit route
            if (window.cur_frm && cur_frm.doc && cur_frm.doc.transit_route) {
                let routes = cur_frm.doc.transit_route;
                if (routes.length > 0) {
                    let html = '<div class="lw-timeline">';
                    routes.forEach(r => {
                        html += `
                            <div class="lw-timeline-item done">
                                <div class="lw-timeline-date">${r.date || ''}</div>
                                <div class="lw-timeline-title">${r.activity || ''}</div>
                                <div class="lw-timeline-desc">${r.location || ''}</div>
                            </div>
                        `;
                    });
                    html += '</div>';
                    $content.html(html);
                } else {
                    $content.html('<div style="text-align: center; color: #8d99a6; padding: 20px 0;">Chưa có dữ liệu hành trình.</div>');
                }
            } else {
                $content.html('<div style="text-align: center; color: #8d99a6; padding: 20px 0;">Đang tải dữ liệu hành trình...</div>');
            }
        } else {
            $content.html('<div style="text-align: center; color: #8d99a6; padding: 20px 0;">Vui lòng mở một mã Theo dõi hành trình (Shipment Tracking) để xem lộ trình chi tiết.</div>');
        }
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

            // Format link text and target
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
