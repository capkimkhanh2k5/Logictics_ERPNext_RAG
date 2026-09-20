(()=>{console.log("SMART WORKFLOW WIDGET SCRIPT LOADED");$(document).ready(function(){let k=[{doctype:"Material Request",id:"wiz-Material-Request",slug:"material-request",label:"1. Y\xEAu c\u1EA7u mua h\xE0ng (Material Request)"},{doctype:"Purchase Order",id:"wiz-Purchase-Order",slug:"purchase-order",label:"2. \u0110\u01A1n \u0111\u1EB7t h\xE0ng (Purchase Order)"},{doctype:"Shipment Tracking",id:"wiz-Shipment-Tracking",slug:"shipment-tracking",label:"3. Theo d\xF5i h\xE0nh tr\xECnh (Shipment Tracking)"},{doctype:"Purchase Receipt",id:"wiz-Purchase-Receipt",slug:"purchase-receipt",label:"4. Nh\u1EADn h\xE0ng (Purchase Receipt)"},{doctype:"Landed Cost Voucher",id:"wiz-Landed-Cost-Voucher",slug:"landed-cost-voucher",label:"5. Ph\xE2n b\u1ED5 gi\xE1 v\u1ED1n (Landed Cost)"},{doctype:"Stock Entry",id:"wiz-Stock-Entry",slug:"stock-entry",label:"6. Nh\u1EADp kho (Stock Entry)"}],T=k.map(e=>e.doctype),o=null,_=null,x=[],m=null,g=null;function E(e){return e==="Air"?`
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#007AFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.2-1.1.6L2.5 8l6.4 3.3L7 15l-3.3-1.1-1.2 1.3 4.2 3.8 3.8 4.2 1.3-1.2L10.7 18.7l3.7-1.9 3.3 6.4 1.2-1.2-.4-2.6Z"/>
                </svg>
            `:e==="Ocean"?`
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0055B3" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M2 21c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1 .6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/>
                    <path d="M19.38 20A11.6 11.6 0 0 0 21 14l-9-4-9 4c0 2.9.94 5.34 2.81 7.76"/>
                    <path d="M19 13V7a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v6"/>
                    <path d="M12 10v4"/>
                    <path d="M12 2v3"/>
                </svg>
            `:`
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#28a745" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="1" y="3" width="15" height="13" rx="2" ry="2"/>
                    <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/>
                    <circle cx="5.5" cy="18.5" r="2.5"/>
                    <circle cx="18.5" cy="18.5" r="2.5"/>
                </svg>
            `}function B(){if($("#lw-fab-container").length===0){let e=`
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
                            ${k.map(t=>`
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
            `;$("body").append(e),$("#lw-fab-main").on("click",function(){$(this).toggleClass("active"),$(this).hasClass("active")?$("#lw-fab-menu").addClass("show"):($("#lw-fab-menu").removeClass("show"),$(".lw-popup").hide())}),$(".lw-sub-fab").on("click",function(){let t=$(this).attr("id").replace("lw-fab-","lw-popup-");$(".lw-popup").hide(),$("#"+t).show(),t==="lw-popup-shipment"&&j()}),$(".lw-popup-close").on("click",function(){if($($(this).data("target")).hide(),g&&(cancelAnimationFrame(g),g=null),o){try{o.remove()}catch(t){}o=null,m=null}})}}function j(){let e=typeof frappe!="undefined"&&frappe.get_route?frappe.get_route():[];e&&e[0]==="Form"&&e[1]&&["Purchase Order","Shipment Tracking","Purchase Receipt"].includes(e[1])&&e[2]?F(e[2],e[1]):S()}function S(){let e=$("#lw-shipment-content");e.html(`
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
                        `);return}let n=`
                        <div style="margin-bottom: 12px;">
                            <strong style="color: #1f272e; font-size: 14px;">Danh s\xE1ch L\xF4 h\xE0ng Qu\u1ED1c t\u1EBF \u0110ang V\u1EADn chuy\u1EC3n:</strong>
                            <div style="font-size: 12px; color: #6c757d;">Nh\u1EA5n v\xE0o \u0111\u01A1n h\xE0ng \u0111\u1EC3 xem b\u1EA3n \u0111\u1ED3 l\u1ED9 tr\xECnh tr\u1EF1c ti\u1EBFp:</div>
                        </div>
                        <div class="lw-shipment-list" style="display: flex; flex-direction: column; gap: 8px;">
                    `;l.forEach(a=>{n+=`
                            <div class="lw-shipment-item" data-name="${a.name}" style="padding: 12px 14px; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; cursor: pointer; transition: all 0.2s;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <strong style="color: #007AFF; font-size: 13px;">${a.name}</strong>
                                    <span class="badge" style="background: #e7f1ff; color: #007AFF; font-weight: 500; font-size: 11px;">${a.status}</span>
                                </div>
                                <div style="font-size: 12px; color: #495057; margin-top: 4px;">
                                    <strong>Nh\xE0 cung c\u1EA5p:</strong> ${a.supplier_name||"N/A"}
                                </div>
                            </div>
                        `}),n+="</div>",e.html(n),$(".lw-shipment-item").hover(function(){$(this).css({background:"#eef5ff","border-color":"#b8d5fd"})},function(){$(this).css({background:"#f8f9fa","border-color":"#e9ecef"})}).on("click",function(){let a=$(this).data("name");F(a,"Purchase Order")})}else e.html('<div style="text-align: center; color: red; padding: 20px;">L\u1ED7i t\u1EA3i danh s\xE1ch v\u1EADn chuy\u1EC3n.</div>')}})}function F(e,t){$("#lw-shipment-content").html(`
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
        `),$("#lw-btn-back-shipments").on("click",function(){if(g&&(cancelAnimationFrame(g),g=null),o){try{o.remove()}catch(n){}o=null,m=null}S()}),frappe.call({method:"logistics_wizard.api.get_shipment_tracking",args:{docname:e,doctype:t},callback:function(n){n.message&&n.message.status==="success"?q(n.message.data,e,t):$("#lw-map-info-text").html(`<span style="color: #d9534f;">${n.message?n.message.message:"Kh\xF4ng th\u1EC3 t\u1EA3i th\xF4ng tin l\u1ED9 tr\xECnh."}</span>`)}})}function O(e){let t=window.L||window.leaflet;if(!t||!o)return;e==="Ocean"||e==="Sea"?(m||(m=t.tileLayer("https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png",{attribution:'Map data: &copy; <a href="http://www.openseamap.org">OpenSeaMap</a> contributors',maxZoom:18,opacity:1})),o.hasLayer(m)||m.addTo(o)):m&&o.hasLayer(m)&&o.removeLayer(m)}function C(e,t,l){let[n,a]=e,[i,s]=t,[d,c]=l,r=c-s,p=d-i;r>180&&(r-=360),r<-180&&(r+=360);let u=a-s,w=n-i;u>180&&(u-=360),u<-180&&(u+=360);let y=r*r+p*p;if(y===0)return Math.hypot(u,w);let f=Math.max(0,Math.min(1,(u*r+w*p)/y)),b=f*r,v=f*p;return Math.hypot(u-b,w-v)}function M(e,t=.002){if(!e||!Array.isArray(e)||e.length<=2)return e||[];let l=0,n=0,a=e.length-1;for(let i=1;i<a;i++){let s=C(e[i],e[0],e[a]);s>l&&(l=s,n=i)}if(l>t){let i=M(e.slice(0,n+1),t),s=M(e.slice(n),t);return i.slice(0,i.length-1).concat(s)}else return[e[0],e[a]]}function I(e,t,l,n){let a=Math.PI/180,i=180/Math.PI,s=e*a,d=l*a,c=(n-t)*a;for(;c>Math.PI;)c-=2*Math.PI;for(;c<-Math.PI;)c+=2*Math.PI;let r=Math.sin(c)*Math.cos(d),p=Math.cos(s)*Math.sin(d)-Math.sin(s)*Math.cos(d)*Math.cos(c);return(Math.atan2(r,p)*i+360)%360}function z(e){let t=[0],l=0;if(!e||e.length<=1)return{cumulative:[0],total:0};for(let n=0;n<e.length-1;n++){let[a,i]=e[n],[s,d]=e[n+1],c=d-i;c>180&&(c-=360),c<-180&&(c+=360);let r=s-a,p=Math.cos((a+s)/2*Math.PI/180);l+=Math.hypot(r,c*p),t.push(l)}return{cumulative:t,total:l}}function P(e,t,l){if(!e||e.length===0)return{point:[0,0],bearing:0};if(e.length===1)return{point:e[0],bearing:0};let n=Math.max(0,Math.min(1,l));if(t.total===0)return{point:e[0],bearing:0};let a=n*t.total,i=0;for(let h=0;h<t.cumulative.length-1;h++)if(a>=t.cumulative[h]&&a<=t.cumulative[h+1]){i=h;break}i>=e.length-1&&(i=e.length-2);let s=t.cumulative[i],d=t.cumulative[i+1]-s,c=d===0?0:Math.max(0,Math.min(1,(a-s)/d)),r=e[i],p=e[i+1]||r,u=r[0]+c*(p[0]-r[0]),w=r[1],f=p[1]-w;f>180&&(f-=360),f<-180&&(f+=360);let b=w+c*f,v=I(r[0],r[1],p[0],p[1]);return{point:[u,b],bearing:v}}function D(e,t,l,n=1500){if(g&&(cancelAnimationFrame(g),g=null),!e||!t||t.length===0)return;let a=z(t),i=typeof e._currentProgress=="number"?e._currentProgress:0,s=Math.max(0,Math.min(1,l)),d=performance.now();function c(r){let p=r-d,u=n<=0?1:Math.min(1,p/n),w=1-Math.pow(1-u,3),y=i+(s-i)*w,{point:f,bearing:b}=P(t,a,y);e.setLatLng(f);let v=e.getElement?e.getElement():null;if(v){let h=v.querySelector(".lw-vehicle-icon-svg")||v.querySelector("svg");h&&(h.style.transform=`rotate(${b}deg)`,h.style.transformOrigin="center center")}e._currentProgress=y,u<1?g=requestAnimationFrame(c):g=null}g=requestAnimationFrame(c)}function q(e,t,l){let n=window.L||window.leaflet;if(!n){$("#lw-map-info-text").html('<span style="color: red;">Th\u01B0 vi\u1EC7n b\u1EA3n \u0111\u1ED3 (Leaflet) ch\u01B0a \u0111\u01B0\u1EE3c t\u1EA3i.</span>');return}if(g&&(cancelAnimationFrame(g),g=null),o){try{o.remove()}catch(G){}o=null,m=null}x=[],_=null,o=n.map("shipment-map",{zoomControl:!0,attributionControl:!0}).setView([20,150],3),n.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",{attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',subdomains:["a","b","c","d"],maxZoom:19}).addTo(o),O(e.method);let a=e.full_route&&e.full_route.length>0?e.full_route:e.route||[];if(!a||a.length===0){$("#lw-map-info-text").html('<span class="text-muted">Ch\u01B0a c\xF3 t\u1ECDa \u0111\u1ED9 n\xE0o \u0111\u01B0\u1EE3c ghi nh\u1EADn cho \u0111\u01A1n h\xE0ng n\xE0y.</span>');return}let i=M(a,.002);(!i||i.length<2)&&(i=a);let s={color:e.method==="Air"?"#007AFF":e.method==="Ocean"?"#0055B3":"#28a745",weight:3.5,opacity:.85,dashArray:e.method==="Air"?"6, 8":e.method==="Ocean"?"8, 4":""};_=n.polyline(i,s).addTo(o);try{o.fitBounds(_.getBounds(),{padding:[40,40],maxZoom:8})}catch(G){}let d=i[0],c=n.divIcon({className:"custom-origin-icon",html:'<div style="background: #28a745; color: white; border-radius: 50%; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.3);">A</div>',iconSize:[26,26],iconAnchor:[13,13]}),r=n.marker(d,{icon:c}).addTo(o);r.bindPopup(`<b>\u0110i\u1EC3m xu\u1EA5t ph\xE1t (Origin):</b><br>${d[0].toFixed(2)}, ${d[1].toFixed(2)}<br><small>${e.origin||""}</small>`),x.push(r);let p=i[i.length-1],u=n.divIcon({className:"custom-dest-icon",html:'<div style="background: #dc3545; color: white; border-radius: 50%; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.3);">B</div>',iconSize:[26,26],iconAnchor:[13,13]}),w=n.marker(p,{icon:u}).addTo(o);w.bindPopup(`<b>\u0110i\u1EC3m \u0111\u1EBFn (Destination):</b><br>${p[0].toFixed(2)}, ${p[1].toFixed(2)}<br><small>${e.destination||""}</small>`),x.push(w);let y=typeof e.progress=="number"?e.progress:.5,f=z(i),b=P(i,f,0),v=n.divIcon({className:"custom-vehicle-icon",html:`
                <div style="background: white; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; box-shadow: 0 3px 10px rgba(0,0,0,0.25); border: 2.5px solid ${e.method==="Air"?"#007AFF":e.method==="Ocean"?"#0055B3":"#28a745"};">
                    <div class="lw-vehicle-icon-svg" style="display: flex; align-items: center; justify-content: center; transform: rotate(${b.bearing}deg); transform-origin: center center;">
                        ${E(e.method)}
                    </div>
                </div>
            `,iconSize:[40,40],iconAnchor:[20,20]}),h=n.marker(b.point,{icon:v,zIndexOffset:1e3}).addTo(o);h._currentProgress=0,h.bindPopup(`<b>V\u1ECB tr\xED hi\u1EC7n t\u1EA1i:</b><br>${e.current_location||"\u0110ang v\u1EADn chuy\u1EC3n"}`),x.push(h),D(h,i,y,1500),setTimeout(()=>{h&&o&&o.hasLayer(h)&&h.openPopup()},1500);let N=e.method==="Air"?"\u2708\uFE0F \u0110\u01B0\u1EDDng h\xE0ng kh\xF4ng (Air)":e.method==="Ocean"?"\u{1F6A2} \u0110\u01B0\u1EDDng bi\u1EC3n (Ocean)":"\u{1F69A} \u0110\u01B0\u1EDDng b\u1ED9 (Road)",W=e.distance_km?` &bull; ${Math.round(e.distance_km).toLocaleString()} km`:"",K=`
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span><strong>Ph\u01B0\u01A1ng th\u1EE9c:</strong> ${N}${W}</span>
                <span class="badge" style="background: #e7f1ff; color: #007AFF;">${e.status_text}</span>
            </div>
            <div><strong>V\u1ECB tr\xED hi\u1EC7n t\u1EA1i:</strong> <span style="color: #007AFF; font-weight: 500;">${e.current_location}</span></div>
        `;$("#lw-map-info-text").html(K),H(t,l),setTimeout(()=>{o&&o.invalidateSize()},300)}function H(e,t){let l=$("#lw-timeline-container");if(window.cur_frm&&cur_frm.doc&&cur_frm.doc.name===e&&cur_frm.doc.transit_route&&cur_frm.doc.transit_route.length>0){L(cur_frm.doc.transit_route,l);return}let n=t,a=e;t==="Purchase Order"?frappe.db.get_value("Shipment Tracking",{purchase_order:e},"name").then(i=>{i&&i.message&&i.message.name?frappe.db.get_doc("Shipment Tracking",i.message.name).then(s=>{L(s.transit_route||[],l)}):l.html('<div style="color: #8d99a6; font-size: 12px; padding: 8px 0;">Ch\u01B0a li\xEAn k\u1EBFt phi\u1EBFu Shipment Tracking ho\u1EB7c ch\u01B0a c\xF3 l\u1ED9 tr\xECnh chi ti\u1EBFt.</div>')}):t==="Shipment Tracking"?frappe.db.get_doc("Shipment Tracking",e).then(i=>{L(i.transit_route||[],l)}):l.html('<div style="color: #8d99a6; font-size: 12px; padding: 8px 0;">Kh\xF4ng c\xF3 d\u1EEF li\u1EC7u l\u1ED9 tr\xECnh.</div>')}function L(e,t){if(!e||e.length===0){t.html('<div style="color: #8d99a6; font-size: 12px; padding: 8px 0;">Ch\u01B0a c\xF3 tr\u1EA1m l\u1ED9 tr\xECnh n\xE0o.</div>');return}let l='<div class="lw-timeline" style="margin-top: 5px;">';e.forEach((n,a)=>{let i=a===e.length-1;l+=`
                <div class="lw-timeline-item done">
                    <div class="lw-timeline-date" style="font-size: 11px; color: #6c757d;">${n.date||""}</div>
                    <div class="lw-timeline-title" style="font-weight: 600; font-size: 13px; color: #1f272e;">${n.activity||""}</div>
                    <div class="lw-timeline-desc" style="font-size: 12px; color: #495057;">\u{1F4CD} ${n.location||""}</div>
                </div>
            `}),l+="</div>",t.html(l)}function A(){k.forEach(e=>{let t=$("#"+e.id);if(t.length){t.removeClass("wiz-step-completed wiz-step-current wiz-step-pending"),t.find(".wiz-check-badge").html("");let l=t.find("a");l.attr("href","/app/"+e.slug),l.text(e.label)}})}function V(e){!e||!e.length||e.forEach(t=>{let l=k.find(d=>d.doctype===t.doctype);if(!l)return;let n=$("#"+l.id);if(!n.length)return;let a=t.label||l.label,i=t.url||"/app/"+l.slug,s=n.find("a");s.attr("href",i),s.text(a),t.completed?(n.addClass("wiz-step-completed"),n.find(".wiz-check-badge").html("\u2714")):t.is_current?n.addClass("wiz-step-current"):n.addClass("wiz-step-pending"),t.is_current&&n.addClass("wiz-step-current")})}function R(){if(B(),typeof frappe=="undefined"||!frappe.get_route)return;let e=frappe.get_route();if(!(!e||!e.length))if(e[0]==="Form"&&e[1]&&T.includes(e[1])&&e[2]){let t=e[1],l=e[2];frappe.call({method:"logistics_wizard.api.get_workflow_chain_status",args:{doctype:t,docname:l},callback:function(n){A(),n&&n.message&&n.message.success&&V(n.message.steps)}})}else if(e[0]==="List"&&e[1]&&T.includes(e[1])){A();let t="wiz-"+e[1].replace(/\s+/g,"-");$("#"+t).addClass("wiz-step-current")}else A()}typeof frappe!="undefined"&&frappe.router&&frappe.router.on("change",R),window.LogisticsWizardMap={douglasPeucker:M,perpendicularDistance:C,calculateBearing:I,computePolylineMetrics:z,interpolateAtProgress:P,animateVehicle:D,update_marine_overlay:O,getShipmentMap:function(){return o},getSeaOverlayLayer:function(){return m},getMapPolyline:function(){return _},getMapMarkers:function(){return x}},setTimeout(R,300)});})();
//# sourceMappingURL=smart_workflow_widget.bundle.E5DTNSYR.js.map
