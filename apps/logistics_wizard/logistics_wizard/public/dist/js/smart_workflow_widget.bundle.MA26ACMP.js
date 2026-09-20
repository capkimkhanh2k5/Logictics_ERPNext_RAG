(()=>{console.log("SMART WORKFLOW WIDGET SCRIPT LOADED");$(document).ready(function(){let S=[{doctype:"Material Request",id:"wiz-Material-Request",slug:"material-request",label:"1. Y\xEAu c\u1EA7u mua h\xE0ng (Material Request)"},{doctype:"Purchase Order",id:"wiz-Purchase-Order",slug:"purchase-order",label:"2. \u0110\u01A1n \u0111\u1EB7t h\xE0ng (Purchase Order)"},{doctype:"Shipment Tracking",id:"wiz-Shipment-Tracking",slug:"shipment-tracking",label:"3. Theo d\xF5i h\xE0nh tr\xECnh (Shipment Tracking)"},{doctype:"Purchase Receipt",id:"wiz-Purchase-Receipt",slug:"purchase-receipt",label:"4. Nh\u1EADn h\xE0ng (Purchase Receipt)"},{doctype:"Landed Cost Voucher",id:"wiz-Landed-Cost-Voucher",slug:"landed-cost-voucher",label:"5. Ph\xE2n b\u1ED5 gi\xE1 v\u1ED1n (Landed Cost)"},{doctype:"Stock Entry",id:"wiz-Stock-Entry",slug:"stock-entry",label:"6. Nh\u1EADp kho (Stock Entry)"}],H=S.map(e=>e.doctype),s=null,N=null,M=[],y=null,g=null;function V(e){return e==="Air"?`
                <svg width="24" height="24" viewBox="0 0 24 24" fill="#007AFF" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 1.5C11.2 1.5 10.6 2.3 10.6 3.2V8.8L2.4 13.5C1.8 13.8 1.5 14.5 1.5 15.1C1.5 15.9 2.2 16.5 3 16.5H10.6V20.2L8.2 21.8C7.9 22 7.7 22.3 7.7 22.7C7.7 23.4 8.3 24 9 24H15C15.7 24 16.3 23.4 16.3 22.7C16.3 22.3 16.1 22 15.8 21.8L13.4 20.2V16.5H21C21.8 16.5 22.5 15.9 22.5 15.1C22.5 14.5 22.2 13.8 21.6 13.5L13.4 8.8V3.2C13.4 2.3 12.8 1.5 12 1.5Z" stroke="#0047AB" stroke-width="0.5"/>
                </svg>
            `:e==="Ocean"?`
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 1 C14.8 3.5 18 8 18 14 V20 C18 21.7 16.7 23 15 23 H9 C7.3 23 6 21.7 6 20 V14 C6 8 9.2 3.5 12 1 Z" fill="#0055B3" stroke="#003380" stroke-width="0.8"/>
                    <rect x="8" y="6.5" width="8" height="2.2" rx="0.4" fill="#38BDF8"/>
                    <rect x="8" y="9.7" width="8" height="2.2" rx="0.4" fill="#BAE6FD"/>
                    <rect x="8" y="12.9" width="8" height="2.2" rx="0.4" fill="#38BDF8"/>
                    <rect x="8" y="16.1" width="8" height="2.2" rx="0.4" fill="#BAE6FD"/>
                    <rect x="8.5" y="19.2" width="7" height="2.6" rx="0.5" fill="#FFFFFF"/>
                    <rect x="10.5" y="20" width="3" height="1" fill="#0055B3"/>
                </svg>
            `:`
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
            `}function K(e){return e==="Ocean"||e==="seaport"||e==="port"?`
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#0055B3" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="5" r="3"/>
                    <line x1="12" y1="22" x2="12" y2="8"/>
                    <path d="M5 12H2a10 10 0 0 0 20 0h-3"/>
                </svg>
            `:`
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#007AFF" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.2-1.1.6L2.5 8l6.4 3.3L7 15l-3.3-1.1-1.2 1.3 4.2 3.8 3.8 4.2 1.3-1.2L10.7 18.7l3.7-1.9 3.3 6.4 1.2-1.2-.4-2.6Z"/>
                </svg>
            `}function J(){if($("#lw-fab-container").length===0){let e=`
                <div id="lw-fab-container">
                    <button class="lw-fab" id="lw-fab-main" title="Tr\u1EE3 l\xFD Logistics & H\u1ED7 tr\u1EE3">
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
                        <span class="fab-close-icon">\u2715</span>
                    </button>
                    <div id="lw-fab-menu">
                        <button class="lw-fab lw-sub-fab" id="lw-fab-workflow" data-tooltip="Ti\u1EBFn tr\xECnh (Workflow)">\u{1F4CB}</button>
                        <button class="lw-fab lw-sub-fab" id="lw-fab-shipment" data-tooltip="H\xE0nh tr\xECnh (Shipment)">\u{1F69A}</button>
                        <button class="lw-fab lw-sub-fab" id="lw-fab-ai" data-tooltip="AI Chat">\u{1F916}</button>
                    </div>
                </div>

                <!-- Popup: Workflow -->
                <div class="lw-popup" id="lw-popup-workflow">
                    <div class="lw-popup-header">
                        Ti\u1EBFn tr\xECnh ch\u1EE9ng t\u1EEB XNK
                        <span class="lw-popup-close" data-target="#lw-popup-workflow">\u2716</span>
                    </div>
                    <div class="lw-popup-body">
                        <ul class="lw-step-list">
                            ${S.map(t=>`
                                <li class="lw-step-item" id="${t.id}">
                                    <span class="wiz-check-badge"></span>
                                    <a href="/app/${t.slug}">${t.label}</a>
                                </li>
                            `).join("")}
                        </ul>
                    </div>
                </div>

                <!-- Popup: Shipment (Map & Timeline) -->
                <div class="lw-popup lw-popup-large" id="lw-popup-shipment">
                    <div class="lw-popup-header">
                        <span>\u{1F5FA}\uFE0F B\u1EA3n \u0111\u1ED3 & H\xE0nh tr\xECnh V\u1EADn chuy\u1EC3n To\xE0n c\u1EA7u</span>
                        <span class="lw-popup-close" data-target="#lw-popup-shipment">\u2716</span>
                    </div>
                    <div class="lw-popup-body" id="lw-shipment-content">
                        <div style="text-align: center; color: #8d99a6; padding: 25px 0;">
                            \u0110ang t\u1EA3i th\xF4ng tin h\xE0nh tr\xECnh...
                        </div>
                    </div>
                </div>

                <!-- Popup: AI Chat -->
                <div class="lw-popup" id="lw-popup-ai">
                    <div class="lw-popup-header">
                        Tr\u1EE3 l\xFD AI Logistics & H\u1EA3i quan
                        <span class="lw-popup-close" data-target="#lw-popup-ai">\u2716</span>
                    </div>
                    <div class="lw-popup-body" style="text-align: center; padding: 30px 15px;">
                        <div style="font-size: 44px; margin-bottom: 12px;">\u{1F916}</div>
                        <h4 style="margin:0 0 10px 0; color: #1f272e;">Tr\u1EE3 l\xFD RAG H\u1EA3i quan</h4>
                        <p style="color: #6c757d; font-size: 13px; line-height: 1.5; margin: 0;">
                            H\u1EC7 th\u1ED1ng AI RAG h\u1ED7 tr\u1EE3 tra c\u1EE9u v\u0103n b\u1EA3n ph\xE1p lu\u1EADt H\u1EA3i quan v\xE0 \u0111\u1EC1 xu\u1EA5t m\xE3 HS Code \u0111ang k\u1EBFt n\u1ED1i!
                        </p>
                    </div>
                </div>
            `;$("body").append(e),$("#lw-fab-main").on("click",function(){$(this).toggleClass("active"),$(this).hasClass("active")?$("#lw-fab-menu").addClass("show"):($("#lw-fab-menu").removeClass("show"),$(".lw-popup").hide())}),$(".lw-sub-fab").on("click",function(){let t=$(this).attr("id").replace("lw-fab-","lw-popup-");$(".lw-popup").hide(),$("#"+t).show(),t==="lw-popup-shipment"&&U()}),$(".lw-popup-close").on("click",function(){if($($(this).data("target")).hide(),g&&(cancelAnimationFrame(g),g=null),s){try{s.remove()}catch(t){}s=null,y=null}})}}function U(){let e=typeof frappe!="undefined"&&frappe.get_route?frappe.get_route():[];e&&e[0]==="Form"&&e[1]&&["Purchase Order","Shipment Tracking","Purchase Receipt"].includes(e[1])&&e[2]?W(e[2],e[1]):j()}function j(){let e=$("#lw-shipment-content");e.html(`
            <div style="text-align: center; padding: 20px; color: #6c757d;">
                <div class="spinner-border text-primary" role="status"></div>
                <div style="margin-top: 10px;">\u0110ang t\u1EA3i danh s\xE1ch l\xF4 h\xE0ng \u0111ang v\u1EADn chuy\u1EC3n...</div>
            </div>
        `),frappe.call({method:"logistics_wizard.api.get_active_shipments",callback:function(t){if(t.message&&t.message.status==="success"){let l=t.message.data||[];if(l.length===0){e.html(`
                            <div style="text-align: center; padding: 35px 20px; color: #8d99a6;">
                                <div style="font-size: 32px; margin-bottom: 8px;">\u{1F4E6}</div>
                                <strong>Kh\xF4ng c\xF3 \u0111\u01A1n h\xE0ng n\xE0o \u0111ang v\u1EADn chuy\u1EC3n.</strong>
                                <p style="font-size: 12px; margin-top: 6px;">H\xE3y t\u1EA1o Purchase Order ho\u1EB7c m\u1EDF m\u1ED9t \u0111\u01A1n h\xE0ng \u0111\u1EC3 xem b\u1EA3n \u0111\u1ED3 h\xE0nh tr\xECnh.</p>
                            </div>
                        `);return}let i=`
                        <div style="margin-bottom: 12px;">
                            <strong style="color: #1f272e; font-size: 14px;">Danh s\xE1ch L\xF4 h\xE0ng Qu\u1ED1c t\u1EBF \u0110ang V\u1EADn chuy\u1EC3n:</strong>
                            <div style="font-size: 12px; color: #6c757d;">Nh\u1EA5n v\xE0o \u0111\u01A1n h\xE0ng \u0111\u1EC3 xem b\u1EA3n \u0111\u1ED3 l\u1ED9 tr\xECnh tr\u1EF1c ti\u1EBFp:</div>
                        </div>
                        <div class="lw-shipment-list" style="display: flex; flex-direction: column; gap: 8px;">
                    `;l.forEach(o=>{i+=`
                            <div class="lw-shipment-item" data-name="${o.name}" style="padding: 12px 14px; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; cursor: pointer; transition: all 0.2s;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <strong style="color: #007AFF; font-size: 13px;">${o.name}</strong>
                                    <span class="badge" style="background: #e7f1ff; color: #007AFF; font-weight: 500; font-size: 11px;">${o.status}</span>
                                </div>
                                <div style="font-size: 12px; color: #495057; margin-top: 4px;">
                                    <strong>Nh\xE0 cung c\u1EA5p:</strong> ${o.supplier_name||"N/A"}
                                </div>
                            </div>
                        `}),i+="</div>",e.html(i),$(".lw-shipment-item").hover(function(){$(this).css({background:"#eef5ff","border-color":"#b8d5fd"})},function(){$(this).css({background:"#f8f9fa","border-color":"#e9ecef"})}).on("click",function(){let o=$(this).data("name");W(o,"Purchase Order")})}else e.html('<div style="text-align: center; color: red; padding: 20px;">L\u1ED7i t\u1EA3i danh s\xE1ch v\u1EADn chuy\u1EC3n.</div>')}})}function W(e,t){$("#lw-shipment-content").html(`
            <div class="lw-map-panel">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <button class="btn btn-xs btn-default" id="lw-btn-back-shipments">\u2190 Quay l\u1EA1i danh s\xE1ch</button>
                    <div style="text-align: right;">
                        <span style="font-size: 11px; color: #6c757d;">${t}:</span>
                        <strong style="color: #007AFF; font-size: 13px; margin-left: 4px;">${e}</strong>
                    </div>
                </div>

                <!-- Map Container -->
                <div id="shipment-map" style="width: 100%; height: 350px; border-radius: 10px; background: #e5e5ea; border: 1px solid #ced4da;"></div>

                <!-- Info Box -->
                <div class="lw-map-info" id="lw-map-info-text" style="padding: 10px 14px; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; font-size: 13px;">
                    <span class="text-muted">\u0110ang ph\xE2n t\xEDch d\u1EEF li\u1EC7u t\u1ECDa \u0111\u1ED9 \u0111\u1ECBa l\xFD v\xE0 d\u1EF1ng l\u1ED9 tr\xECnh...</span>
                </div>

                <!-- Detailed Timeline -->
                <div>
                    <div style="font-weight: 600; font-size: 13px; color: #343a40; margin-bottom: 8px;">
                        L\u1ED9 tr\xECnh V\u1EADn chuy\u1EC3n Chi ti\u1EBFt (Transit Checkpoints):
                    </div>
                    <div id="lw-timeline-container" style="max-height: 180px; overflow-y: auto;"></div>
                </div>
            </div>
        `),$("#lw-btn-back-shipments").on("click",function(){if(g&&(cancelAnimationFrame(g),g=null),s){try{s.remove()}catch(i){}s=null,y=null}j()}),frappe.call({method:"logistics_wizard.api.get_shipment_tracking",args:{docname:e,doctype:t},callback:function(i){i.message&&i.message.status==="success"?ee(i.message.data,e,t):$("#lw-map-info-text").html(`<span style="color: #d9534f;">${i.message?i.message.message:"Kh\xF4ng th\u1EC3 t\u1EA3i th\xF4ng tin l\u1ED9 tr\xECnh."}</span>`)}})}function G(e){let t=window.L||window.leaflet;if(!t||!s)return;e==="Ocean"||e==="Sea"?(y||(y=t.tileLayer("https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png",{attribution:'Map data: &copy; <a href="http://www.openseamap.org">OpenSeaMap</a> contributors',maxZoom:18,opacity:1})),s.hasLayer(y)||y.addTo(s)):y&&s.hasLayer(y)&&s.removeLayer(y)}function Z(e,t,l){let[i,o]=e,[n,r]=t,[h,c]=l,a=c-r,d=h-n;a>180&&(a-=360),a<-180&&(a+=360);let u=o-r,b=i-n;u>180&&(u-=360),u<-180&&(u+=360);let C=a*a+d*d;if(C===0)return Math.hypot(u,b);let f=Math.max(0,Math.min(1,(u*a+b*d)/C)),F=f*a,v=f*d;return Math.hypot(u-F,b-v)}function z(e,t=.002){if(!e||!Array.isArray(e)||e.length<=2)return e||[];let l=0,i=0,o=e.length-1;for(let n=1;n<o;n++){let r=Z(e[n],e[0],e[o]);r>l&&(l=r,i=n)}if(l>t){let n=z(e.slice(0,i+1),t),r=z(e.slice(i),t);return n.slice(0,n.length-1).concat(r)}else return[e[0],e[o]]}function X(e,t,l,i){let o=Math.PI/180,n=180/Math.PI,r=e*o,h=l*o,c=(i-t)*o;for(;c>Math.PI;)c-=2*Math.PI;for(;c<-Math.PI;)c+=2*Math.PI;let a=Math.sin(c)*Math.cos(h),d=Math.cos(r)*Math.sin(h)-Math.sin(r)*Math.cos(h)*Math.cos(c);return(Math.atan2(a,d)*n+360)%360}function O(e){let t=[0],l=0;if(!e||e.length<=1)return{cumulative:[0],total:0};for(let i=0;i<e.length-1;i++){let[o,n]=e[i],[r,h]=e[i+1],c=h-n;c>180&&(c-=360),c<-180&&(c+=360);let a=r-o,d=Math.cos((o+r)/2*Math.PI/180);l+=Math.hypot(a,c*d),t.push(l)}return{cumulative:t,total:l}}function B(e,t,l){if(!e||e.length===0)return{point:[0,0],bearing:0};if(e.length===1)return{point:e[0],bearing:0};let i=Math.max(0,Math.min(1,l));if(t.total===0)return{point:e[0],bearing:0};let o=i*t.total,n=0;for(let w=0;w<t.cumulative.length-1;w++)if(o>=t.cumulative[w]&&o<=t.cumulative[w+1]){n=w;break}n>=e.length-1&&(n=e.length-2);let r=t.cumulative[n],h=t.cumulative[n+1]-r,c=h===0?0:Math.max(0,Math.min(1,(o-r)/h)),a=e[n],d=e[n+1]||a,u=a[0]+c*(d[0]-a[0]),b=a[1],f=d[1]-b;f>180&&(f-=360),f<-180&&(f+=360);let F=b+c*f,v=X(a[0],a[1],d[0],d[1]);return{point:[u,F],bearing:v}}function Q(e,t,l,i=1500,o=[],n=[0,.05,.95,1],r="Ocean"){if(g&&(cancelAnimationFrame(g),g=null),!e||!t||t.length===0)return;let h=O(t),c=typeof e._currentProgress=="number"?e._currentProgress:0,a=Math.max(0,Math.min(1,l)),d=performance.now(),u=n&&n.length>1?n[1]:.05,b=n&&n.length>2?n[2]:.95;function C(f){let F=f-d,v=i<=0?1:Math.min(1,F/i),w=1-Math.pow(1-v,3),A=c+(a-c)*w,{point:R,bearing:D}=B(t,h,A);e.setLatLng(R);let k="Road",m="Ch\u1EB7ng 1: V\u1EADn chuy\u1EC3n \u0111\u01B0\u1EDDng b\u1ED9 (First-mile Road)",L="#FF9500";A<=u?(k="Road",m="Ch\u1EB7ng 1: Xe t\u1EA3i container v\u1EADn chuy\u1EC3n ra C\u1EA3ng/S\xE2n bay xu\u1EA5t ph\xE1t",L="#FF9500"):A<=b?(k=r,m=r==="Air"?"Ch\u1EB7ng 2: M\xE1y bay v\u1EADn t\u1EA3i \u0111ang bay qua kh\xF4ng ph\u1EADn Qu\u1ED1c t\u1EBF (Air Transit)":"Ch\u1EB7ng 2: T\xE0u container \u0111ang v\u01B0\u1EE3t h\u1EA3i tr\xECnh Th\xE1i B\xECnh D\u01B0\u01A1ng (Ocean Transit)",L=r==="Air"?"#007AFF":"#0055B3"):(k="Road",m="Ch\u1EB7ng 3: Xe t\u1EA3i container giao nh\u1EADn v\u1EC1 Kho C\xE1p Kim Kh\xE1nh \u0110\xE0 N\u1EB5ng (Last-mile Road)",L="#FF9500");let T=e.getElement?e.getElement():null;if(T){if(e._activeMode!==k){e._activeMode=k;let p=T.querySelector(".lw-vehicle-box");p&&(p.style.borderColor=L);let _=T.querySelector(".lw-vehicle-icon-svg");if(_&&(_.innerHTML=V(k)),e.getPopup&&e.getPopup()){let x=k==="Ocean"?"T\xE0u bi\u1EC3n \u{1F6A2}":k==="Air"?"M\xE1y bay \u2708\uFE0F":"Xe t\u1EA3i Container \u{1F69A}";e.setPopupContent(`<b>Ph\u01B0\u01A1ng ti\u1EC7n: ${x}</b><br>${m}<br><small>Ti\u1EBFn tr\xECnh to\xE0n tr\xECnh: ${(A*100).toFixed(1)}%</small>`)}}let P=T.querySelector(".lw-vehicle-icon-svg")||T.querySelector("svg");P&&(P.style.transform=`rotate(${D}deg)`,P.style.transformOrigin="center center")}e._currentProgress=A,v<1?g=requestAnimationFrame(C):g=null}g=requestAnimationFrame(C)}function ee(e,t,l){let i=window.L||window.leaflet;if(!i){$("#lw-map-info-text").html('<span style="color: red;">Th\u01B0 vi\u1EC7n b\u1EA3n \u0111\u1ED3 (Leaflet) ch\u01B0a \u0111\u01B0\u1EE3c t\u1EA3i.</span>');return}if(g&&(cancelAnimationFrame(g),g=null),s){try{s.remove()}catch(p){}s=null,y=null}M=[],N=null,s=i.map("shipment-map",{zoomControl:!0,attributionControl:!0}).setView([20,150],3),i.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',subdomains:["a","b","c"],maxZoom:19}).addTo(s),G(e.method);let o=e.full_route&&e.full_route.length>0?e.full_route:e.route||[];if(!o||o.length===0){$("#lw-map-info-text").html('<span class="text-muted">Ch\u01B0a c\xF3 t\u1ECDa \u0111\u1ED9 n\xE0o \u0111\u01B0\u1EE3c ghi nh\u1EADn cho \u0111\u01A1n h\xE0ng n\xE0y.</span>');return}let n=z(o,.002);(!n||n.length<2)&&(n=o);let r=[];if(e.legs&&Array.isArray(e.legs)&&e.legs.length>0&&e.legs.forEach(p=>{let _=p.coordinates_latlon||[];if(_.length>=2){let x=z(_,.002);(!x||x.length<2)&&(x=_);let q=p.mode==="Road",ne=p.mode==="Air",le=q?"#FF9500":ne?"#007AFF":"#0055B3",oe=q?"6, 8":"",re=q?3.5:4,se=i.polyline(x,{color:le,weight:re,opacity:.92,dashArray:oe}).addTo(s);r.push(se)}}),r.length===0){let p=i.polyline(n,{color:e.method==="Air"?"#007AFF":e.method==="Ocean"?"#0055B3":"#FF9500",weight:3.5,opacity:.9,dashArray:e.method==="Road"?"6, 8":""}).addTo(s);r.push(p)}try{let p=i.featureGroup(r);s.fitBounds(p.getBounds(),{padding:[40,40],maxZoom:8})}catch(p){}let h=n[0],c=e.origin&&e.origin.name||(typeof e.origin=="string"?e.origin:"Kho nh\xE0 m\xE1y xu\u1EA5t ph\xE1t"),a=i.divIcon({className:"custom-origin-icon",html:'<div style="background: #28a745; color: white; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 800; border: 2.5px solid white; box-shadow: 0 3px 8px rgba(0,0,0,0.35); cursor: pointer;" title="\u0110i\u1EC3m xu\u1EA5t ph\xE1t (Origin - \u0110i\u1EC3m O)">O</div>',iconSize:[28,28],iconAnchor:[14,14]}),d=i.marker(h,{icon:a}).addTo(s);d.bindPopup(`<b>Kho xu\u1EA5t ph\xE1t (Origin - \u0110i\u1EC3m O):</b><br>${c}<br><small>To\u1EA1 \u0111\u1ED9: ${h[0].toFixed(4)}, ${h[1].toFixed(4)}</small>`),M.push(d);let u=n[n.length-1],b=e.destination&&e.destination.name||(typeof e.destination=="string"?e.destination:"Kho Logistics C\xE1p Kim Kh\xE1nh \u0110\xE0 N\u1EB5ng"),C=i.divIcon({className:"custom-dest-icon",html:'<div style="background: #dc3545; color: white; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 800; border: 2.5px solid white; box-shadow: 0 3px 8px rgba(0,0,0,0.35); cursor: pointer;" title="\u0110i\u1EC3m \u0111\xEDch \u0111\u1EBFn (Destination - \u0110i\u1EC3m D)">D</div>',iconSize:[28,28],iconAnchor:[14,14]}),f=i.marker(u,{icon:C}).addTo(s);if(f.bindPopup(`<b>Kho \u0111\xEDch nh\u1EADn h\xE0ng (Destination - \u0110i\u1EC3m D):</b><br>${b}<br><small>To\u1EA1 \u0111\u1ED9: ${u[0].toFixed(4)}, ${u[1].toFixed(4)}</small>`),M.push(f),e.departure_hub&&e.departure_hub.coordinates){let p=e.departure_hub.coordinates,_=i.divIcon({className:"custom-dep-hub-icon",html:`<div style="background: white; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; border: 2.5px solid ${e.method==="Air"?"#007AFF":"#0055B3"}; box-shadow: 0 2px 6px rgba(0,0,0,0.25); cursor: pointer;" title="Tr\u1EA1m trung chuy\u1EC3n xu\u1EA5t ph\xE1t">
                    ${K(e.method)}
                </div>`,iconSize:[30,30],iconAnchor:[15,15]}),x=i.marker([p[0],p[1]],{icon:_}).addTo(s);x.bindPopup(`<b>Tr\u1EA1m trung chuy\u1EC3n xu\u1EA5t ph\xE1t:</b><br>${e.departure_hub.name||"C\u1EA3ng/S\xE2n bay xu\u1EA5t"}<br><small>To\u1EA1 \u0111\u1ED9: ${p[0].toFixed(4)}, ${p[1].toFixed(4)}</small>`),M.push(x)}if(e.arrival_hub&&e.arrival_hub.coordinates){let p=e.arrival_hub.coordinates,_=i.divIcon({className:"custom-arr-hub-icon",html:`<div style="background: white; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; border: 2.5px solid ${e.method==="Air"?"#007AFF":"#0055B3"}; box-shadow: 0 2px 6px rgba(0,0,0,0.25); cursor: pointer;" title="Tr\u1EA1m trung chuy\u1EC3n \u0111\u1EBFn">
                    ${K(e.method)}
                </div>`,iconSize:[30,30],iconAnchor:[15,15]}),x=i.marker([p[0],p[1]],{icon:_}).addTo(s);x.bindPopup(`<b>Tr\u1EA1m trung chuy\u1EC3n \u0111\u1EBFn:</b><br>${e.arrival_hub.name||"C\u1EA3ng/S\xE2n bay \u0111\u1EBFn"}<br><small>To\u1EA1 \u0111\u1ED9: ${p[0].toFixed(4)}, ${p[1].toFixed(4)}</small>`),M.push(x)}let F=typeof e.progress=="number"?e.progress:.55,v=e.progress_thresholds||[0,.05,.95,1],w="Road";F>v[1]&&F<=v[2]&&(w=e.method);let A=w==="Road"?"#FF9500":e.method==="Air"?"#007AFF":"#0055B3",R=O(n),D=B(n,R,0),k=i.divIcon({className:"custom-vehicle-icon",html:`
                <div class="lw-vehicle-box" style="background: white; border-radius: 50%; width: 42px; height: 42px; display: flex; align-items: center; justify-content: center; box-shadow: 0 3px 10px rgba(0,0,0,0.3); border: 2.8px solid ${A}; transition: border-color 0.3s;">
                    <div class="lw-vehicle-icon-svg" style="display: flex; align-items: center; justify-content: center; transform: rotate(${D.bearing}deg); transform-origin: center center;">
                        ${V(w)}
                    </div>
                </div>
            `,iconSize:[42,42],iconAnchor:[21,21]}),m=i.marker(D.point,{icon:k,zIndexOffset:1e3}).addTo(s);m._currentProgress=0,m._activeMode=w,m.bindPopup(`<b>V\u1ECB tr\xED ph\u01B0\u01A1ng ti\u1EC7n:</b><br>${e.current_location||"\u0110ang v\u1EADn chuy\u1EC3n"}`),M.push(m),Q(m,n,F,1600,e.legs||[],v,e.method),setTimeout(()=>{m&&s&&s.hasLayer(m)&&m.openPopup()},1600);let L=e.method==="Air"?"\u2708\uFE0F \u0110a ph\u01B0\u01A1ng th\u1EE9c H\xE0ng kh\xF4ng (Air Multimodal)":e.method==="Ocean"?"\u{1F6A2} \u0110a ph\u01B0\u01A1ng th\u1EE9c \u0110\u01B0\u1EDDng bi\u1EC3n (Ocean Multimodal)":"\u{1F69A} \u0110\u01B0\u1EDDng b\u1ED9 (Inland Road)",T=e.distance_km?` &bull; ${Math.round(e.distance_km).toLocaleString()} km`:"",P=`
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span><strong>M\xF4 h\xECnh:</strong> ${L}${T}</span>
                <span class="badge" style="background: #e7f1ff; color: #007AFF;">${e.status_text}</span>
            </div>
            <div><strong>V\u1ECB tr\xED hi\u1EC7n t\u1EA1i:</strong> <span style="color: #007AFF; font-weight: 500;">${e.current_location}</span></div>
        `;$("#lw-map-info-text").html(P),te(t,l),setTimeout(()=>{s&&s.invalidateSize()},300)}function te(e,t){let l=$("#lw-timeline-container");if(window.cur_frm&&cur_frm.doc&&cur_frm.doc.name===e&&cur_frm.doc.transit_route&&cur_frm.doc.transit_route.length>0){I(cur_frm.doc.transit_route,l);return}let i=t,o=e;t==="Purchase Order"?frappe.db.get_value("Shipment Tracking",{purchase_order:e},"name").then(n=>{n&&n.message&&n.message.name?frappe.db.get_doc("Shipment Tracking",n.message.name).then(r=>{I(r.transit_route||[],l)}):l.html('<div style="color: #8d99a6; font-size: 12px; padding: 8px 0;">Ch\u01B0a li\xEAn k\u1EBFt phi\u1EBFu Shipment Tracking ho\u1EB7c ch\u01B0a c\xF3 l\u1ED9 tr\xECnh chi ti\u1EBFt.</div>')}):t==="Shipment Tracking"?frappe.db.get_doc("Shipment Tracking",e).then(n=>{I(n.transit_route||[],l)}):l.html('<div style="color: #8d99a6; font-size: 12px; padding: 8px 0;">Kh\xF4ng c\xF3 d\u1EEF li\u1EC7u l\u1ED9 tr\xECnh.</div>')}function I(e,t){if(!e||e.length===0){t.html('<div style="color: #8d99a6; font-size: 12px; padding: 8px 0;">Ch\u01B0a c\xF3 tr\u1EA1m l\u1ED9 tr\xECnh n\xE0o.</div>');return}let l='<div class="lw-timeline" style="margin-top: 5px;">';e.forEach((i,o)=>{let n=o===e.length-1;l+=`
                <div class="lw-timeline-item done">
                    <div class="lw-timeline-date" style="font-size: 11px; color: #6c757d;">${i.date||""}</div>
                    <div class="lw-timeline-title" style="font-weight: 600; font-size: 13px; color: #1f272e;">${i.activity||""}</div>
                    <div class="lw-timeline-desc" style="font-size: 12px; color: #495057;">\u{1F4CD} ${i.location||""}</div>
                </div>
            `}),l+="</div>",t.html(l)}function E(){S.forEach(e=>{let t=$("#"+e.id);if(t.length){t.removeClass("wiz-step-completed wiz-step-current wiz-step-pending"),t.find(".wiz-check-badge").html("");let l=t.find("a");l.attr("href","/app/"+e.slug),l.text(e.label)}})}function ie(e){!e||!e.length||e.forEach(t=>{let l=S.find(h=>h.doctype===t.doctype);if(!l)return;let i=$("#"+l.id);if(!i.length)return;let o=t.label||l.label,n=t.url||"/app/"+l.slug,r=i.find("a");r.attr("href",n),r.text(o),t.completed?(i.addClass("wiz-step-completed"),i.find(".wiz-check-badge").html("\u2714")):t.is_current?i.addClass("wiz-step-current"):i.addClass("wiz-step-pending"),t.is_current&&i.addClass("wiz-step-current")})}function Y(){if(J(),typeof frappe=="undefined"||!frappe.get_route)return;let e=frappe.get_route();if(!(!e||!e.length))if(e[0]==="Form"&&e[1]&&H.includes(e[1])&&e[2]){let t=e[1],l=e[2];frappe.call({method:"logistics_wizard.api.get_workflow_chain_status",args:{doctype:t,docname:l},callback:function(i){E(),i&&i.message&&i.message.success&&ie(i.message.steps)}})}else if(e[0]==="List"&&e[1]&&H.includes(e[1])){E();let t="wiz-"+e[1].replace(/\s+/g,"-");$("#"+t).addClass("wiz-step-current")}else E()}typeof frappe!="undefined"&&frappe.router&&frappe.router.on("change",Y),window.LogisticsWizardMap={douglasPeucker:z,perpendicularDistance:Z,calculateBearing:X,computePolylineMetrics:O,interpolateAtProgress:B,animateVehicle:Q,update_marine_overlay:G,getShipmentMap:function(){return s},getSeaOverlayLayer:function(){return y},getMapPolyline:function(){return N},getMapMarkers:function(){return M}},setTimeout(Y,300)});})();
//# sourceMappingURL=smart_workflow_widget.bundle.MA26ACMP.js.map
