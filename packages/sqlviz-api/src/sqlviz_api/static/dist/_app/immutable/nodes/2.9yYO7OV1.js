const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["../chunks/ekk7sIKj.js","../chunks/CXyBGMYu.js","../chunks/C0jHkEur.js","../chunks/Cea5cxJJ.js","../assets/editor.B8tIeeJt.css"])))=>i.map(i=>d[i]);
import{b as ra,a as g,f as M,c as X,d as oa}from"../chunks/EVBMHDXH.js";import{w as At,o as Jt,a as ia}from"../chunks/DxICD3qh.js";import{h as Me,i as It,e as Et,b5 as la,b as ca,E as da,ab as va,f as ua,c as ha,s as Bt,d as Pt,S as _a,L as fa,b6 as ga,P as pa,al as ma,aj as ut,b7 as Ht,R as Rt,b8 as ba,w as e,b9 as je,a3 as ya,t as Je,F as G,G as dt,z as i,y as c,B as o,x as Xe,K as V,I as B,v as O,ba as Xt,D as v,bb as wa,bc as $a,a4 as Ce,u as ka}from"../chunks/C0jHkEur.js";import{f as xa,a as Ct,d as te,s as N,e as Zt}from"../chunks/CY52XHtr.js";import{l as J,p as Ne,s as oe,a as ea,c as kt,b as Ca}from"../chunks/ds6XAry9.js";import{i as z}from"../chunks/DfobnKYw.js";import{s as Y,a as xt,c as jt,d as Ye,r as Ma,b as Sa}from"../chunks/DL6DCHt6.js";import{g as Na}from"../chunks/D3rk13n2.js";import{a as Ae,i as vt,e as wt,F as Ta,D as Ea}from"../chunks/D9jE4LIp.js";import{c as Pa,_ as Da}from"../chunks/CXyBGMYu.js";import{B as La}from"../chunks/Cea5cxJJ.js";function ae(f,t,u,h,_){var d;Me&&It();var y=(d=t.$$slots)==null?void 0:d[u],s=!1;y===!0&&(y=t.children,s=!0),y===void 0||y(f,s?()=>h:h)}function Ia(f,t,u,h,_,y){let s=Me;Me&&It();var d=null;Me&&Et.nodeType===la&&(d=Et,It());var p=Me?Et:f,k=new La(p,!1);ca(()=>{const T=t()||null;var R=ga;if(T===null){k.ensure(null,null);return}return k.ensure(T,q=>{if(T){if(d=Me?d:va(T,R),ra(d,d),h){var H=null;Me&&xa(T)&&d.append(H=document.createComment(""));var D=Me?ua(d):d.appendChild(ha());Me&&(D===null?Bt(!1):Pt(D)),h(d,D),H==null||H.remove()}_a.nodes.end=d,q.before(d)}Me&&Pt(q)}),()=>{}},da),fa(()=>{}),s&&(Bt(!0),Pt(p))}function ta(f=!1){const t=pa,u=t.l.u;if(!u)return;let h=()=>je(t.s);if(f){let _=0,y={};const s=ya(()=>{let d=!1;const p=t.s;for(const k in p)p[k]!==y[k]&&(y[k]=p[k],d=!0);return d&&_++,_});h=()=>e(s)}u.b.length&&ma(()=>{Ut(t,h),Ht(u.b)}),ut(()=>{const _=Rt(()=>u.m.map(ba));return()=>{for(const y of _)typeof y=="function"&&y()}}),u.a.length&&ut(()=>{Ut(t,h),Ht(u.a)})}function Ut(f,t){if(f.l.s)for(const u of f.l.s)e(u);t()}var Ra=M('<div class="no-data svelte-7vbfso"><p class="svelte-7vbfso">Score available after dashboard execution.</p> <p class="hint svelte-7vbfso">V0.2 backend required for utility scoring.</p></div>'),qa=M('<span class="low-good-hint svelte-7vbfso">(low=good)</span>'),za=M('<div class="breakdown-row svelte-7vbfso"><span class="dim-name svelte-7vbfso"> </span> <div class="mini-track svelte-7vbfso"><div class="mini-fill svelte-7vbfso"></div></div> <span> <!></span></div>'),Aa=M('<div class="breakdown-block svelte-7vbfso"></div>'),Oa=M('<button class="action-btn apply svelte-7vbfso">Apply</button>'),Ba=M('<div class="suggestion svelte-7vbfso"><div class="suggestion-text svelte-7vbfso"><span class="warn-icon svelte-7vbfso">⚠</span> <div><strong> </strong> <span class="suggestion-body svelte-7vbfso"> </span> <span class="impact svelte-7vbfso"> </span></div></div> <div class="suggestion-actions svelte-7vbfso"><!> <button class="action-btn dismiss svelte-7vbfso">Dismiss</button></div></div>'),Ha=M('<div class="suggestions-block svelte-7vbfso"><span class="suggestions-label svelte-7vbfso">Sugerencias</span> <!></div>'),ja=M('<div class="utility-block svelte-7vbfso"><div class="score-row svelte-7vbfso"><span class="score-heading svelte-7vbfso">Utility Score</span> <span> </span></div> <div class="score-track svelte-7vbfso"><div class="score-fill svelte-7vbfso"></div></div></div> <!> <!>',1),Ua=M('<aside class="score-panel svelte-7vbfso" aria-label="Dashboard Score"><div class="panel-header svelte-7vbfso"><span class="panel-title svelte-7vbfso">Dashboard Score</span> <button class="close-btn svelte-7vbfso" aria-label="Close score panel">×</button></div> <!></aside>');function Fa(f,t){Je(t,!0);function u(w){return w>=85?{text:"Excellent",cls:"excellent"}:w>=70?{text:"Good",cls:"good"}:w>=55?{text:"Fair",cls:"fair"}:{text:"Needs work",cls:"needs-work"}}const h=V(()=>Math.round((t.layout.utility_score??0)*100)),_=V(()=>u(e(h))),y=V(()=>(t.layout.suggestions??[]).slice().sort((w,L)=>L.score_impact-w.score_impact)),s=V(()=>t.layout.utility_breakdown??{}),d=V(()=>t.layout.utility_score!=null);let p=G(dt(new Set));const k=V(()=>e(y).filter(w=>!e(p).has(w.panel_id+w.suggestion)));function T(w){v(p,new Set([...e(p),w.panel_id+w.suggestion]),!0)}var R=Ua(),q=i(R),H=c(i(q),2);o(q);var D=c(q,2);{var m=w=>{var L=Ra();g(w,L)},E=w=>{var L=ja(),A=B(L),S=i(A),x=c(i(S),2),Q=i(x);o(x),o(S);var ye=c(S,2),we=i(ye);o(ye),o(A);var Le=c(A,2);{var Te=ve=>{var F=Aa();Ae(F,21,()=>Object.entries(e(s)),([ue,Z])=>ue,(ue,Z)=>{var j=V(()=>Xt(e(Z),2));let ge=()=>e(j)[0],pe=()=>e(j)[1];const Ee=V(()=>Math.round(Number(pe())*100)),$e=V(()=>ge()==="cognitive_load"||ge()==="space_waste");var he=za(),le=i(he),Pe=i(le,!0);o(le);var ke=c(le,2),Ie=i(ke);o(ke);var _e=c(ke,2);let De;var ce=i(_e),Re=c(ce);{var ne=se=>{var xe=qa();g(se,xe)};z(Re,se=>{e($e)&&se(ne)})}o(_e),o(he),O(se=>{N(Pe,ge()),xt(Ie,`width: ${e(Ee)??""}%`),De=Y(_e,1,"dim-value svelte-7vbfso",null,De,{"low-good":e($e)}),N(ce,`${se??""} `)},[()=>Number(pe()).toFixed(2)]),g(ue,he)}),o(F),g(ve,F)},Ue=V(()=>Object.keys(e(s)).length>0);z(Le,ve=>{e(Ue)&&ve(Te)})}var Oe=c(Le,2);{var Fe=ve=>{var F=Ha(),ue=c(i(F),2);Ae(ue,17,()=>e(k),Z=>Z.panel_id+Z.suggestion,(Z,j)=>{var ge=Ba(),pe=i(ge),Ee=c(i(pe),2),$e=i(Ee),he=i($e,!0);o($e);var le=c($e,2),Pe=i(le);o(le);var ke=c(le,2),Ie=i(ke);o(ke),o(Ee),o(pe);var _e=c(pe,2),De=i(_e);{var ce=ne=>{var se=Oa();te("click",se,()=>{var xe;return(xe=t.onApplySuggestion)==null?void 0:xe.call(t,e(j).panel_id,e(j).action)}),g(ne,se)};z(De,ne=>{e(j).action&&t.onApplySuggestion&&ne(ce)})}var Re=c(De,2);o(_e),o(ge),O(ne=>{N(he,e(j).panel_label??e(j).panel_id),N(Pe,`— ${e(j).suggestion??""}`),N(Ie,`(+${ne??""}% utility)`)},[()=>Math.round(e(j).score_impact*100)]),te("click",Re,()=>T(e(j))),g(Z,ge)}),o(F),g(ve,F)};z(Oe,ve=>{e(k).length>0&&ve(Fe)})}O(()=>{Y(x,1,`score-value ${e(_).cls??""}`,"svelte-7vbfso"),N(Q,`${e(h)??""} / 100 · ${e(_).text??""}`),xt(we,`width: ${e(h)??""}%`)}),g(w,L)};z(D,w=>{e(d)?w(E,-1):w(m)})}o(R),te("click",H,function(...w){var L;(L=t.onClose)==null||L.apply(this,w)}),g(f,R),Xe()}Ct(["click"]);wa();/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 * 
 * Copyright (c) 2026 Lucide Icons and Contributors
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The following Lucide icons are derived from the Feather project:
 * 
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 * 
 * The MIT License (MIT) (for the icons listed above)
 * 
 * Copyright (c) 2013-present Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const Wa={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 * 
 * Copyright (c) 2026 Lucide Icons and Contributors
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The following Lucide icons are derived from the Feather project:
 * 
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 * 
 * The MIT License (MIT) (for the icons listed above)
 * 
 * Copyright (c) 2013-present Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const Va=f=>{for(const t in f)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 * 
 * Copyright (c) 2026 Lucide Icons and Contributors
 * 
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 * 
 * ---
 * 
 * The following Lucide icons are derived from the Feather project:
 * 
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 * 
 * The MIT License (MIT) (for the icons listed above)
 * 
 * Copyright (c) 2013-present Cole Bemis
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 */const Ft=(...f)=>f.filter((t,u,h)=>!!t&&t.trim()!==""&&h.indexOf(t)===u).join(" ").trim();var Ga=oa("<svg><!><!></svg>");function ie(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]),h=J(u,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);Je(t,!1);let _=Ne(t,"name",8,void 0),y=Ne(t,"color",8,"currentColor"),s=Ne(t,"size",8,24),d=Ne(t,"strokeWidth",8,2),p=Ne(t,"absoluteStrokeWidth",8,!1),k=Ne(t,"iconNode",24,()=>[]);ta();var T=Ga();jt(T,(H,D,m)=>({...Wa,...H,...h,width:s(),height:s(),stroke:y(),"stroke-width":D,class:m}),[()=>Va(h)?void 0:{"aria-hidden":"true"},()=>(je(p()),je(d()),je(s()),Rt(()=>p()?Number(d())*24/Number(s()):d())),()=>(je(Ft),je(_()),je(u),Rt(()=>Ft("lucide-icon","lucide",_()?`lucide-${_()}`:"",u.class)))]);var R=i(T);Ae(R,1,k,vt,(H,D)=>{var m=V(()=>Xt(e(D),2));let E=()=>e(m)[0],w=()=>e(m)[1];var L=X(),A=B(L);Ia(A,E,!0,(S,x)=>{jt(S,()=>({...w()}))}),g(H,L)});var q=c(R);ae(q,t,"default",{}),o(T),g(f,T),Xe()}function aa(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const h=[["path",{d:"M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"}]];ie(f,oe({name:"activity"},()=>u,{get iconNode(){return h},children:(_,y)=>{var s=X(),d=B(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function Qa(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const h=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"M7 11h8"}],["path",{d:"M7 16h3"}],["path",{d:"M7 6h12"}]];ie(f,oe({name:"chart-bar-decreasing"},()=>u,{get iconNode(){return h},children:(_,y)=>{var s=X(),d=B(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function $t(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const h=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"M7 16h8"}],["path",{d:"M7 11h12"}],["path",{d:"M7 6h3"}]];ie(f,oe({name:"chart-bar"},()=>u,{get iconNode(){return h},children:(_,y)=>{var s=X(),d=B(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function na(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const h=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"m19 9-5 5-4-4-3 3"}]];ie(f,oe({name:"chart-line"},()=>u,{get iconNode(){return h},children:(_,y)=>{var s=X(),d=B(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function Ka(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const h=[["path",{d:"M21 12c.552 0 1.005-.449.95-.998a10 10 0 0 0-8.953-8.951c-.55-.055-.998.398-.998.95v8a1 1 0 0 0 1 1z"}],["path",{d:"M21.21 15.89A10 10 0 1 1 8 2.83"}]];ie(f,oe({name:"chart-pie"},()=>u,{get iconNode(){return h},children:(_,y)=>{var s=X(),d=B(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function Ya(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const h=[["circle",{cx:"7.5",cy:"7.5",r:".5",fill:"currentColor"}],["circle",{cx:"18.5",cy:"5.5",r:".5",fill:"currentColor"}],["circle",{cx:"11.5",cy:"11.5",r:".5",fill:"currentColor"}],["circle",{cx:"7.5",cy:"16.5",r:".5",fill:"currentColor"}],["circle",{cx:"17.5",cy:"14.5",r:".5",fill:"currentColor"}],["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}]];ie(f,oe({name:"chart-scatter"},()=>u,{get iconNode(){return h},children:(_,y)=>{var s=X(),d=B(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function Dt(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const h=[["line",{x1:"4",x2:"20",y1:"9",y2:"9"}],["line",{x1:"4",x2:"20",y1:"15",y2:"15"}],["line",{x1:"10",x2:"8",y1:"3",y2:"21"}],["line",{x1:"16",x2:"14",y1:"3",y2:"21"}]];ie(f,oe({name:"hash"},()=>u,{get iconNode(){return h},children:(_,y)=>{var s=X(),d=B(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function Ot(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const h=[["rect",{width:"7",height:"9",x:"3",y:"3",rx:"1"}],["rect",{width:"7",height:"5",x:"14",y:"3",rx:"1"}],["rect",{width:"7",height:"9",x:"14",y:"12",rx:"1"}],["rect",{width:"7",height:"5",x:"3",y:"16",rx:"1"}]];ie(f,oe({name:"layout-dashboard"},()=>u,{get iconNode(){return h},children:(_,y)=>{var s=X(),d=B(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function Wt(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const h=[["path",{d:"M2 5h20"}],["path",{d:"M6 12h12"}],["path",{d:"M9 19h6"}]];ie(f,oe({name:"list-filter"},()=>u,{get iconNode(){return h},children:(_,y)=>{var s=X(),d=B(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function Ja(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const h=[["path",{d:"M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"}]];ie(f,oe({name:"table-2"},()=>u,{get iconNode(){return h},children:(_,y)=>{var s=X(),d=B(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function be(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const h=[["path",{d:"M16 7h6v6"}],["path",{d:"m22 7-8.5 8.5-5-5L2 17"}]];ie(f,oe({name:"trending-up"},()=>u,{get iconNode(){return h},children:(_,y)=>{var s=X(),d=B(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function Lt(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const h=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]];ie(f,oe({name:"triangle-alert"},()=>u,{get iconNode(){return h},children:(_,y)=>{var s=X(),d=B(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function Vt(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const h=[["path",{d:"M10 14.66v1.626a2 2 0 0 1-.976 1.696A5 5 0 0 0 7 21.978"}],["path",{d:"M14 14.66v1.626a2 2 0 0 0 .976 1.696A5 5 0 0 1 17 21.978"}],["path",{d:"M18 9h1.5a1 1 0 0 0 0-5H18"}],["path",{d:"M4 22h16"}],["path",{d:"M6 9a6 6 0 0 0 12 0V3a1 1 0 0 0-1-1H7a1 1 0 0 0-1 1z"}],["path",{d:"M6 9H4.5a1 1 0 0 1 0-5H6"}]];ie(f,oe({name:"trophy"},()=>u,{get iconNode(){return h},children:(_,y)=>{var s=X(),d=B(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function Se(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
 * @license lucide-svelte v1.0.1 - ISC
 *
 * ISC License
 *
 * Copyright (c) 2026 Lucide Icons and Contributors
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * ---
 *
 * The following Lucide icons are derived from the Feather project:
 *
 * airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out
 *
 * The MIT License (MIT) (for the icons listed above)
 *
 * Copyright (c) 2013-present Cole Bemis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 */const h=[["path",{d:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"}],["path",{d:"M16 3.128a4 4 0 0 1 0 7.744"}],["path",{d:"M22 21v-2a4 4 0 0 0-3-3.87"}],["circle",{cx:"9",cy:"7",r:"4"}]];ie(f,oe({name:"users"},()=>u,{get iconNode(){return h},children:(_,y)=>{var s=X(),d=B(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}const Gt={kpi_overview:Dt,kpi_performance:be,financial_kpi:Dt,sales_kpi:Dt,hr_overview:Se,trend_analysis:be,financial_trend:be,product_growth:be,sales_performance:be,marketing_performance:be,hr_trend:be,ops_monitoring:aa,user_lifecycle:Se,user_retention:Se,retention_analysis:Se,cohort_analysis:Se,product_retention:Se,funnel_analysis:Wt,product_funnel:Wt,financial_dashboard:be,financial_comparison:$t,sales_dashboard:be,sales_ranking:Vt,marketing_analytics:na,marketing_comparison:$t,product_analytics:Se,hr_analytics:Se,comparison_analysis:$t,competitive_analysis:$t,ranking_analysis:Vt,distribution_analysis:Qa,correlation_analysis:Ya,composition_analysis:Ka,anomaly_detection:Lt,anomaly_monitoring:Lt,incident_monitoring:Lt,data_detail:Ja,analytics_overview:Ot},Qt={finance:be,product:Se,marketing:na,hr:Se,ops:aa,sales:be,analytics:Ot};function Xa(f,t,u){return f&&Gt[f]?Gt[f]:t&&Qt[t]?Qt[t]:Ot}var Za=M('<li><button><span class="panel-icon svelte-609rsk"><!></span> <span class="panel-title svelte-609rsk"> </span></button></li>'),en=M('<nav class="dashboard-sidebar svelte-609rsk" aria-label="Dashboard navigation"><div class="sidebar-label svelte-609rsk">Dashboards</div> <ul class="panel-list svelte-609rsk"></ul></nav>');function tn(f,t){Je(t,!0);let u=Ne(t,"activeId",3,null);var h=en(),_=c(i(h),2);Ae(_,21,()=>t.items,y=>y.id,(y,s)=>{const d=V(()=>Xa(e(s).dashboard_hint,e(s).dashboard_domain));var p=Za(),k=i(p);let T;var R=i(k),q=i(R);Pa(q,()=>e(d),(m,E)=>{E(m,{size:14})}),o(R);var H=c(R,2),D=i(H,!0);o(H),o(k),o(p),O(()=>{T=Y(k,1,"panel-item svelte-609rsk",null,T,{active:e(s).id===u()}),Ye(k,"title",e(s).name),N(D,e(s).name)}),te("click",k,()=>{var m;return(m=t.onSelect)==null?void 0:m.call(t,e(s).id)}),g(y,p)}),o(_),o(h),g(f,h),Xe()}Ct(["click"]);const qt=At(null);var an=M('<div class="banner fallback svelte-10vh4gh"><span class="banner-icon svelte-10vh4gh">⚠</span> <div><strong class="svelte-10vh4gh">Inference without data</strong> <p class="svelte-10vh4gh"> </p></div></div>'),nn=M('<div class="intent-desc svelte-10vh4gh"> </div>'),sn=M('<li class="signal-item svelte-10vh4gh"><span class="signal-dot svelte-10vh4gh">✓</span> <span class="signal-name svelte-10vh4gh"> </span> <span class="signal-score svelte-10vh4gh"> </span></li>'),rn=M('<div class="subsection-title svelte-10vh4gh">Key signals</div> <ul class="signal-list svelte-10vh4gh"></ul>',1),on=M('<p class="muted-note svelte-10vh4gh">Signal data unavailable — run the panel to see details.</p>'),Kt=M('<div class="score-row svelte-10vh4gh"><span> </span> <div class="bar-track svelte-10vh4gh"><div></div></div> <span> </span></div>'),ln=M('<div class="subsection-title svelte-10vh4gh">Intent scores</div> <div class="score-bars svelte-10vh4gh"></div>',1),cn=M('<p class="chart-desc svelte-10vh4gh"> </p>'),dn=M('<div class="subsection-title svelte-10vh4gh">Chart scores</div> <div class="score-bars svelte-10vh4gh"></div>',1),vn=M('<li class="error-item svelte-10vh4gh"> </li>'),un=M('<div class="subsection-title svelte-10vh4gh">Errors</div> <ul class="error-list svelte-10vh4gh"></ul>',1),hn=M('<div class="backdrop svelte-10vh4gh" role="presentation"></div> <aside class="explain-drawer svelte-10vh4gh" aria-label="Explainability panel"><div class="drawer-header svelte-10vh4gh"><h2 class="drawer-title svelte-10vh4gh">Why this chart?</h2> <button class="close-btn svelte-10vh4gh" aria-label="Close">✕</button></div> <div class="drawer-body svelte-10vh4gh"><!> <section class="section svelte-10vh4gh"><h3 class="section-title svelte-10vh4gh">Detected intent</h3> <div class="intent-badge svelte-10vh4gh"><span class="intent-icon svelte-10vh4gh"> </span> <div><div class="intent-name svelte-10vh4gh"> </div> <!></div></div> <!> <!></section> <section class="section svelte-10vh4gh"><h3 class="section-title svelte-10vh4gh">Selected chart</h3> <div class="chart-badge svelte-10vh4gh"><strong class="svelte-10vh4gh"> </strong> <!></div> <!></section> <section class="section svelte-10vh4gh"><h3 class="section-title svelte-10vh4gh">Inference confidence</h3> <div class="quality-row svelte-10vh4gh"><span> </span></div> <p class="quality-detail svelte-10vh4gh"> </p> <!></section> <div class="debug-row svelte-10vh4gh"><span class="debug-item svelte-10vh4gh">fingerprint: <code class="svelte-10vh4gh"> </code></span> <span class="debug-item svelte-10vh4gh"> </span> <span class="debug-item svelte-10vh4gh"> </span></div></div></aside>',1);function _n(f,t){Je(t,!1);const u=()=>kt(qt,"$explainTarget",h),[h,_]=ea(),y={has_group_by:"Groups results with GROUP BY",has_order_by:"Results are ordered sequentially",has_order_by_desc:"Results ordered descending (ranking)",has_limit:"Uses TOP/LIMIT (top-N records)",has_aggregation:"Uses aggregation (SUM, COUNT, AVG…)",has_sum:"Uses SUM aggregate",has_count:"Uses COUNT aggregate",has_avg:"Uses AVG aggregate",has_window_function:"Window function (RANK, ROW_NUMBER…)",has_cte:"Uses Common Table Expression (WITH…)",has_join:"Joins multiple tables",has_where:"Filters data with WHERE",has_date_column:"Contains a date/time column",has_numeric_column:"Contains numeric columns",has_string_column:"Contains text/string columns",has_single_numeric_column:"Returns a single numeric value",has_two_numeric_columns:"Returns two numeric columns (x/y pair)",has_temporal_dimension:"Temporal grouping (date/time)",has_geographic_dimension:"Geographic grouping (location)",has_revenue_metric:"Revenue or monetary metric detected",has_product_entity:"Product or item entity detected",has_customer_entity:"Customer or user entity detected",has_distinct:"Uses DISTINCT",has_case_when:"Contains CASE WHEN logic",has_outliers:"Data contains statistical outliers",has_outliers_detected:"Outlier values detected in results",has_partition_by:"Uses PARTITION BY",has_subquery:"Contains a subquery",result_row_count_is_1:"Returns exactly 1 row (single metric)",result_column_count_is_1:"Returns exactly 1 column",result_is_wide_table:"Wide table — many columns, general data",numeric_column_ratio:"High proportion of numeric columns",date_column_ratio:"High proportion of date columns",row_count_normalized:"Number of result rows (non-zero)",cardinality_ratio:"Category uniqueness ratio",temporal_cardinality:"Distinct time periods in result",trend_strength:"Statistical trend detected in values",no_group_by:"No GROUP BY clause",no_aggregation:"No aggregate functions",no_temporal_dimension:"No temporal dimension present",no_order_by_desc:"Not ordered descending",no_numeric_column:"No numeric output columns",no_case_when:"No conditional logic",no_customer_entity:"No customer entity found",no_count:"No COUNT aggregate",order_desc_and_limit:"Top-N ranking pattern (DESC + LIMIT)",high_cardinality:"Many unique categories",low_cardinality:"Few distinct categories",multiple_rows:"Returns multiple rows",single_numeric_column:"Single numeric column in result",high_col_count:"Many columns selected",group_by_count_gte_2:"Groups by 2 or more dimensions",part_of_whole_score:"Part-of-whole pattern (share/percentage)",is_monotonic_decreasing:"Values consistently decrease (funnel)",distinct_entity_count_over_time:"Distinct users counted over time (retention)",has_percentile:"Uses percentile/quantile function"},s={trend:{label:"Temporal Trend",icon:"↗",description:"Values change over time. The SQL groups by a date or sequential column with an ORDER BY."},comparison:{label:"Comparison",icon:"⇄",description:"Values compared across distinct categories such as products, regions or segments."},kpi:{label:"Key Metric (KPI)",icon:"#",description:"A single aggregate number — the SQL returns one summary value with no GROUP BY."},distribution:{label:"Distribution",icon:"∿",description:"How values are spread across a range or bucket (histogram-style data)."},geospatial:{label:"Geographic",icon:"⊕",description:"Data has a geographic dimension such as country, region or coordinates."},relationship:{label:"Correlation",icon:"◎",description:"Two numeric dimensions that may be correlated — scatter-plot pattern."},composition:{label:"Composition",icon:"◔",description:"Parts that add up to a whole — market share, budget split, category breakdown."},retention:{label:"Retention / Cohort",icon:"⟲",description:"Tracks how many users or customers return over time (COUNT DISTINCT over temporal)."},funnel:{label:"Funnel",icon:"▽",description:"Sequential steps where values consistently decrease — conversion or drop-off."},ranking:{label:"Ranking / Top-N",icon:"▲",description:"Top values sorted descending with a LIMIT — leaderboard or best performers."},detail:{label:"Tabular Detail",icon:"≡",description:"General table of records with no clear analytical pattern."},anomaly:{label:"Anomaly Detection",icon:"!",description:"Highlights outlier or unusual values in the data."}},d={line:{label:"Line Chart",description:"Shows how a value evolves over time or a sequential dimension."},bar:{label:"Bar Chart",description:"Compares discrete values across categories side by side."},bar_horizontal:{label:"Horizontal Bar",description:"Same as bar but rotated — better when category labels are long."},pie:{label:"Pie Chart",description:"Shows each category as a fraction of the total."},scatter:{label:"Scatter Plot",description:"Reveals correlations between two numeric variables."},histogram:{label:"Histogram",description:"Distribution of a single numeric variable across value buckets."},table:{label:"Table",description:"Presents all records when no single visualization fits better."},kpi:{label:"KPI Card",description:"A single headline number — the most important metric, front and center."}},p={high:{label:"High confidence",cls:"positive",detail:"The SQL pattern clearly matches the detected intent. This visualization is highly reliable."},medium:{label:"Medium confidence",cls:"neutral",detail:"The SQL pattern partially matches. The result is likely correct but some ambiguity exists."},low:{label:"Low confidence",cls:"negative",detail:"The SQL pattern is ambiguous. Consider rephrasing your query for clearer inference."}};function k(S){return S.explanation.filter(x=>x.contribution>0).sort((x,Q)=>Q.contribution-x.contribution).slice(0,5)}function T(S){return y[S]??S.replace(/_/g," ")}function R(S){return s[S]??{label:S,icon:"?",description:""}}function q(S){return d[S]??{label:S,description:""}}function H(S){return p[S]??p.low}function D(S,x){return x===0?"4%":Math.max(4,Math.round(S/x*100))+"%"}function m(){qt.set(null)}function E(S){S.key==="Escape"&&m()}ta();var w=X();Zt("keydown",$a,E);var L=B(w);{var A=S=>{const x=Ce(()=>u().inference_result),Q=Ce(()=>k(e(x))),ye=Ce(()=>R(e(x).intent_winner)),we=Ce(()=>q(e(x).chart_winner)),Le=Ce(()=>H(e(x).chart_quality)),Te=Ce(()=>[{intent:e(x).intent_winner,raw_score:e(x).intent_raw_score},...e(x).intent_alternatives]),Ue=Ce(()=>Math.max(...e(Te).map(C=>C.raw_score),.01)),Oe=Ce(()=>e(x).chart_alternatives),Fe=Ce(()=>[{chart:e(x).chart_winner,raw_score:e(x).chart_raw_score},...e(Oe)]),ve=Ce(()=>Math.max(...e(Fe).map(C=>C.raw_score),.01));var F=hn(),ue=B(F),Z=c(ue,2),j=i(Z),ge=c(i(j),2);o(j);var pe=c(j,2),Ee=i(pe);{var $e=C=>{var P=an(),U=c(i(P),2),fe=c(i(U),2),K=i(fe,!0);o(fe),o(U),o(P),O(()=>N(K,e(x).fallback_reason||"The query could not be executed, so inference ran on SQL structure only.")),g(C,P)};z(Ee,C=>{e(x).fallback_applied&&C($e)})}var he=c(Ee,2),le=c(i(he),2),Pe=i(le),ke=i(Pe,!0);o(Pe);var Ie=c(Pe,2),_e=i(Ie),De=i(_e,!0);o(_e);var ce=c(_e,2);{var Re=C=>{var P=nn(),U=i(P,!0);o(P),O(()=>N(U,e(ye).description)),g(C,P)};z(ce,C=>{e(ye).description&&C(Re)})}o(Ie),o(le);var ne=c(le,2);{var se=C=>{var P=rn(),U=c(B(P),2);Ae(U,5,()=>e(Q),vt,(fe,K)=>{var W=sn(),ee=c(i(W),2),de=i(ee,!0);o(ee);var n=c(ee,2),a=i(n,!0);o(n),o(W),O((r,l)=>{N(de,r),N(a,l)},[()=>T(e(K).signal),()=>e(K).contribution.toFixed(2)]),g(fe,W)}),o(U),g(C,P)},xe=C=>{var P=on();g(C,P)};z(ne,C=>{e(Q).length>0?C(se):C(xe,-1)})}var ht=c(ne,2);{var Mt=C=>{var P=ln(),U=c(B(P),2);Ae(U,5,()=>e(Te),vt,(fe,K,W)=>{var ee=Kt(),de=i(ee);Y(de,1,"score-label svelte-10vh4gh",null,{},{winner:W===0});var n=i(de,!0);o(de);var a=c(de,2),r=i(a);Y(r,1,"bar-fill svelte-10vh4gh",null,{},{"bar-winner":W===0}),o(a);var l=c(a,2);Y(l,1,"score-value svelte-10vh4gh",null,{},{winner:W===0});var $=i(l,!0);o(l),o(ee),O((b,I,re)=>{N(n,b),xt(r,`width: ${I??""}`),N($,re)},[()=>R(e(K).intent).label,()=>D(e(K).raw_score,e(Ue)),()=>e(K).raw_score.toFixed(2)]),g(fe,ee)}),o(U),g(C,P)};z(ht,C=>{e(Te).length>1&&C(Mt)})}o(he);var Ze=c(he,2),et=c(i(Ze),2),tt=i(et),_t=i(tt,!0);o(tt);var ft=c(tt,2);{var St=C=>{var P=cn(),U=i(P,!0);o(P),O(()=>N(U,e(we).description)),g(C,P)};z(ft,C=>{e(we).description&&C(St)})}o(et);var at=c(et,2);{var nt=C=>{var P=dn(),U=c(B(P),2);Ae(U,5,()=>e(Fe),vt,(fe,K,W)=>{var ee=Kt(),de=i(ee);Y(de,1,"score-label svelte-10vh4gh",null,{},{winner:W===0});var n=i(de,!0);o(de);var a=c(de,2),r=i(a);Y(r,1,"bar-fill svelte-10vh4gh",null,{},{"bar-winner":W===0}),o(a);var l=c(a,2);Y(l,1,"score-value svelte-10vh4gh",null,{},{winner:W===0});var $=i(l,!0);o(l),o(ee),O((b,I,re)=>{N(n,b),xt(r,`width: ${I??""}`),N($,re)},[()=>q(e(K).chart).label,()=>D(e(K).raw_score,e(ve)),()=>e(K).raw_score.toFixed(2)]),g(fe,ee)}),o(U),g(C,P)};z(at,C=>{e(Oe).length>0&&C(nt)})}o(Ze);var We=c(Ze,2),Ve=c(i(We),2),Ge=i(Ve),Be=i(Ge,!0);o(Ge),o(Ve);var st=c(Ve,2),gt=i(st,!0);o(st);var pt=c(st,2);{var Nt=C=>{var P=un(),U=c(B(P),2);Ae(U,5,()=>e(x).errors,vt,(fe,K)=>{var W=vn(),ee=i(W,!0);o(W),O(()=>N(ee,e(K))),g(fe,W)}),o(U),g(C,P)};z(pt,C=>{e(x).errors.length>0&&C(Nt)})}o(We);var Qe=c(We,2),Ke=i(Qe),mt=c(i(Ke)),bt=i(mt);o(mt),o(Ke);var rt=c(Ke,2),ot=i(rt,!0);o(rt);var it=c(rt,2),Tt=i(it);o(it),o(Qe),o(pe),o(Z),O((C,P)=>{N(ke,e(ye).icon),N(De,e(ye).label),N(_t,e(we).label),Y(Ge,1,`quality-badge ${e(Le).cls??""}`,"svelte-10vh4gh"),N(Be,e(Le).label),N(gt,e(Le).detail),N(bt,`${C??""}…`),N(ot,e(x).engine_version),N(Tt,`${P??""} ms`)},[()=>e(x).fingerprint.slice(0,12),()=>e(x).elapsed_ms.toFixed(1)]),te("click",ue,m),te("keydown",ue,()=>{}),te("click",ge,m),g(S,F)};z(L,S=>{u()&&S(A)})}g(f,w),Xe(),_()}Ct(["click","keydown"]);const zt=At({});var fn=M('<div class="editor-loading svelte-1dhf0v9">Loading editor…</div>'),gn=M('<div class="editor-host svelte-1dhf0v9"><!> <div></div></div>');function pn(f,t){Je(t,!0);let u=Ne(t,"value",15,""),h=Ne(t,"disabled",3,!1),_=Ne(t,"theme",3,"dark"),y,s=null,d=null,p=G(!1),k=!1;Jt(async()=>{window.MonacoEnvironment||(window.MonacoEnvironment={getWorker(m,E){return new Worker(URL.createObjectURL(new Blob(["self.onmessage=function(){}"],{type:"text/javascript"})))}});try{const m=await Da(()=>import("../chunks/ekk7sIKj.js").then(E=>E.b),__vite__mapDeps([0,1,2,3,4]),import.meta.url);m.editor.defineTheme("sqlviz-dark",{base:"vs-dark",inherit:!0,rules:[{token:"keyword",foreground:"a78bfa"},{token:"string",foreground:"22c55e"},{token:"comment",foreground:"64748b",fontStyle:"italic"},{token:"number",foreground:"f59e0b"}],colors:{"editor.background":"#0f172a","editor.foreground":"#f1f5f9","editor.lineHighlightBackground":"#1e293b","editor.selectionBackground":"#6366f133","editorLineNumber.foreground":"#475569","editorLineNumber.activeForeground":"#94a3b8","editorCursor.foreground":"#6366f1","scrollbarSlider.background":"#334155","scrollbarSlider.hoverBackground":"#475569","editorBracketMatch.background":"#6366f120","editorBracketMatch.border":"#6366f1"}}),m.editor.defineTheme("sqlviz-light",{base:"vs",inherit:!0,rules:[{token:"keyword",foreground:"4f46e5"},{token:"string",foreground:"16a34a"},{token:"comment",foreground:"64748b",fontStyle:"italic"},{token:"number",foreground:"d97706"}],colors:{"editor.background":"#ffffff","editor.foreground":"#0f172a","editor.lineHighlightBackground":"#f8fafc","editor.selectionBackground":"#6366f133","editorLineNumber.foreground":"#94a3b8","editorLineNumber.activeForeground":"#64748b","editorCursor.foreground":"#6366f1","scrollbarSlider.background":"#e2e8f0","scrollbarSlider.hoverBackground":"#cbd5e1","editorBracketMatch.background":"#6366f120","editorBracketMatch.border":"#6366f1"}}),s=m.editor.create(y,{value:u(),language:"sql",theme:_()==="light"?"sqlviz-light":"sqlviz-dark",minimap:{enabled:!1},fontSize:13,fontFamily:"'JetBrains Mono', 'Cascadia Code', 'Fira Code', 'Consolas', monospace",lineNumbers:"on",scrollBeyondLastLine:!1,wordWrap:"off",tabSize:4,renderLineHighlight:"line",padding:{top:12,bottom:12},folding:!1,lineNumbersMinChars:3,glyphMargin:!1,overviewRulerLanes:0}),s.addCommand(m.KeyMod.CtrlCmd|m.KeyCode.Enter,()=>{var E;return(E=t.onRun)==null?void 0:E.call(t)}),s.addCommand(m.KeyMod.CtrlCmd|m.KeyCode.KeyS,()=>{var E;return(E=t.onRun)==null?void 0:E.call(t)}),s.onDidChangeModelContent(()=>{k=!0,u(s.getValue()),k=!1}),zt.set({focusStatement(E){if(!s)return;const w=s.getModel();if(!w)return;const L=s.getValue();let A=0;if(E>0){let x=0;for(let Q=0;Q<L.length;Q++)if(L[Q]===";"&&(x++,x===E)){A=Q+1;break}for(;A<L.length&&(L[A]===`
`||L[A]==="\r"||L[A]===" ");)A++}const S=w.getPositionAt(A);s.revealLineInCenter(S.lineNumber),s.setPosition(S),s.focus()}}),d=m,v(p,!0),requestAnimationFrame(()=>{s==null||s.layout(),s==null||s.focus()})}catch(m){console.error("[SQLEditor] Monaco init failed:",m),v(p,!0)}}),ia(()=>{zt.set({}),s==null||s.dispose(),s=null}),ut(()=>{if(s&&!k&&s.getValue()!==u()){const m=s.getPosition();s.setValue(u()),m&&s.setPosition(m)}}),ut(()=>{s&&s.updateOptions({readOnly:h()})}),ut(()=>{!e(p)||!d||!s||d.editor.setTheme(_()==="light"?"sqlviz-light":"sqlviz-dark")});var T=gn(),R=i(T);{var q=m=>{var E=fn();g(m,E)};z(R,m=>{e(p)||m(q)})}var H=c(R,2);let D;Ca(H,m=>y=m,()=>y),o(T),O(()=>D=Y(H,1,"editor-container svelte-1dhf0v9",null,D,{hidden:!e(p)})),g(f,T),Xe()}const Yt=At({});var mn=M('<span class="dash-name svelte-1uha8ag"> </span>'),bn=M('<form class="new-dash-form svelte-1uha8ag"><input class="new-dash-input svelte-1uha8ag" placeholder="Dashboard name"/> <button type="submit" class="new-dash-confirm svelte-1uha8ag">Create</button> <button type="button" class="new-dash-cancel svelte-1uha8ag">✕</button></form>'),yn=M('<button class="new-dash-btn svelte-1uha8ag">+ New</button>'),wn=M('<button title="Dashboard Score"> </button>'),$n=M('<div class="error-chip svelte-1uha8ag"><span>✕</span> <span class="error-text svelte-1uha8ag"> </span></div>'),kn=M('<span class="exec-inline svelte-1uha8ag"> </span>'),xn=M('<div class="editor-section svelte-1uha8ag"><div class="editor-toolbar svelte-1uha8ag"><button class="run-btn svelte-1uha8ag"><span>▶</span> </button> <kbd class="shortcut svelte-1uha8ag">Ctrl+Enter</kbd> <!></div> <div class="editor-wrapper svelte-1uha8ag"><!></div></div>'),Cn=M('<div class="state-msg svelte-1uha8ag"><span class="spinner svelte-1uha8ag">⟳</span> <span> </span></div>'),Mn=M('<p class="hint svelte-1uha8ag">Separate multiple queries with <code class="svelte-1uha8ag">;</code> — each becomes a panel</p>'),Sn=M('<div class="empty-state svelte-1uha8ag"><div class="empty-arrow svelte-1uha8ag">⬇</div> <p class="svelte-1uha8ag"> </p> <!></div>'),Nn=M('<div class="toast svelte-1uha8ag" role="status" aria-live="polite"> </div>'),Tn=M('<div class="app-shell svelte-1uha8ag"><header class="app-bar svelte-1uha8ag"><div class="bar-left svelte-1uha8ag"><span class="app-logo svelte-1uha8ag">SQLviz</span> <!> <!></div> <div class="bar-right svelte-1uha8ag"><!> <div class="mode-toggle svelte-1uha8ag" role="group" aria-label="Dashboard mode"><button>Preview</button> <button>Edit</button></div> <button class="theme-btn svelte-1uha8ag"> </button></div></header> <div class="app-body svelte-1uha8ag"><!> <div class="app-main svelte-1uha8ag"><!> <!> <div><!></div></div> <!></div></div> <!> <!>',1);function Hn(f,t){Je(t,!0);const u=()=>kt(zt,"$editorRef",y),h=()=>kt(Yt,"$filterValues",y),_=()=>kt(wt,"$editMode",y),[y,s]=ea();let d=G(""),p=G(null),k=G(!1),T=G(null),R=G(null),q=G("dark");function H(){v(q,e(q)==="dark"?"light":"dark",!0),e(q)==="light"?document.documentElement.dataset.theme="light":delete document.documentElement.dataset.theme,localStorage.setItem("sqlviz-theme",e(q))}let D=G(null),m=G(dt([])),E=G(dt([])),w=G(dt([])),L=G(!1),A=G(dt([])),S=G(!1),x=G(""),Q=G(null),ye=0;const we=V(()=>e(p)!==null&&e(p).rows.length>0),Le=V(()=>e(A).length>=2),Te=V(()=>e(A).find(n=>n.id===e(D))??null),Ue=V(()=>{var n;return((n=e(p))==null?void 0:n.utility_score)!=null?Math.round(e(p).utility_score*100):null}),Oe=V(()=>{const n=new Set,a=[];for(const r of e(w))for(const l of r.inference_result.filter_controls)n.has(l.variable)||(n.add(l.variable),a.push(l));return a}),Fe=V(()=>e(Oe).length>0);let ve=0;async function F(n,a){const r=await fetch(n,{method:"POST",headers:a!==void 0?{"Content-Type":"application/json"}:{},body:a!==void 0?JSON.stringify(a):void 0});if(!r.ok){const l=await r.json().catch(()=>null);throw new Error((l==null?void 0:l.detail)??`${r.status} ${r.statusText}`)}return r.json()}async function ue(n,a){const r=await fetch(n,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify(a)});if(!r.ok){const l=await r.json().catch(()=>null);throw new Error((l==null?void 0:l.detail)??`${r.status} ${r.statusText}`)}return r.json()}async function Z(n){const a=n.map($=>({panel_id:$.panel_id,inference_result:$.inference_result})),r=await F("/api/v1/compose",a),l=new Map(n.map($=>[$.panel_id,$.data]));return{...r,rows:r.rows.map($=>({panels:$.panels.map(b=>({...b,data:l.get(b.panel_id)??[]}))}))}}Jt(async()=>{localStorage.getItem("sqlviz-theme")==="light"&&(v(q,"light"),document.documentElement.dataset.theme="light");const a=await fetch("/api/v1/auth/me");if(a.status===401){await Na("/login");return}const r=await a.json();r.demo&&wt.set(!0);try{const l=await fetch("/api/v1/dashboards").then(b=>b.json());if(v(A,l,!0),l.length===0){if(r.demo){const{sql:b}=await fetch("/api/v1/demo/sql").then(I=>I.json());v(d,b,!0),j()}return}v(D,l[0].id,!0);const $=await fetch(`/api/v1/panels?dashboard_id=${e(D)}`).then(b=>b.json());if($.length===0)return;$.sort((b,I)=>b.sort_order-I.sort_order),v(m,$.map(b=>b.id),!0),v(E,$.map(b=>b.sql_content),!0),v(d,e(E).join(`;

`),!0)}catch{}});async function j(){if(e(k))return;const n=e(d).split(";").map(l=>l.trim()).filter(l=>l.length>0);if(n.length===0){v(R,'No SQL statements found. Write at least one query separated by ";".');return}v(k,!0),v(R,null);let a=e(D);const r=[...e(m)];try{a||(a=(await F("/api/v1/dashboards",{name:"My Dashboard",sort_order:0})).id,v(D,a,!0));const l=[],$=[];for(let b=0;b<n.length;b++){const I=n[b];v(T,`Statement ${b+1} / ${n.length}…`);let re;r[b]?(await ue(`/api/v1/panels/${r[b]}`,{sql_content:I,sort_order:b}),re=r[b]):re=(await F("/api/v1/panels",{dashboard_id:a,name:`Panel ${b+1}`,sql_content:I,sort_order:b})).id,$.push(re);const lt=await F(`/api/v1/panels/${re}/execute`);l.push({panel_id:re,...lt})}if(e(D)!==a){v(T,null);return}v(m,$,!0),v(E,n,!0),v(w,l,!0),v(T,"Composing layout…"),v(p,await Z(l),!0),v(T,null);try{v(A,await fetch("/api/v1/dashboards").then(b=>b.json()),!0)}catch{}}catch(l){v(R,l instanceof Error?l.message:String(l),!0),v(T,null)}finally{v(k,!1)}}async function ge(n){const a=e(m).indexOf(n);if(a<0)return;try{await fetch(`/api/v1/panels/${n}`,{method:"DELETE"})}catch{ce("Delete failed — check the API server.");return}const r=e(w).filter((b,I)=>I!==a),l=e(m).filter((b,I)=>I!==a),$=e(E).filter((b,I)=>I!==a);if(v(w,r,!0),v(m,l,!0),v(E,$,!0),v(d,$.join(`;

`),!0),r.length===0){v(p,null);return}try{v(p,await Z(r),!0)}catch(b){ce(b instanceof Error?b.message:"Compose failed after delete.")}}function pe(n){var r,l;const a=e(m).indexOf(n);a<0||(l=(r=u()).focusStatement)==null||l.call(r,a)}function Ee(n){const a=e(w).find(r=>r.panel_id===n);if(!a){ce("Run the dashboard first to see explainability data.");return}qt.set(a)}async function $e(){const n=e(x).trim()||"New Dashboard";v(S,!1),v(x,"");try{const a=await F("/api/v1/dashboards",{name:n,sort_order:e(A).length});v(A,await fetch("/api/v1/dashboards").then(r=>r.json()),!0),v(D,a.id,!0),v(m,[],!0),v(E,[],!0),v(d,""),v(w,[],!0),v(p,null)}catch(a){ce(a instanceof Error?a.message:"Could not create dashboard.")}}function he(){v(S,!1),v(x,"")}async function le(n){if(!(n===e(D)||e(k)))try{const a=await fetch(`/api/v1/panels?dashboard_id=${n}`).then(r=>r.json());a.sort((r,l)=>r.sort_order-l.sort_order),v(D,n,!0),v(m,a.map(r=>r.id),!0),v(E,a.map(r=>r.sql_content),!0),v(d,e(E).join(`;

`),!0),v(w,[],!0),v(p,null),a.length>0&&j()}catch(a){ce(a instanceof Error?a.message:"Could not load dashboard.")}}async function Pe(n,a){try{await ue(`/api/v1/panels/${n}/override`,{field_name:"chart_type",user_value:a});const r=await F(`/api/v1/panels/${n}/execute`);v(w,e(w).map(l=>l.panel_id===n?{panel_id:n,inference_result:r.inference_result,data:r.data}:l),!0),v(p,await Z(e(w)),!0)}catch(r){ce(r instanceof Error?r.message:"Chart override failed.")}}function ke(n,a){e(p)&&v(p,{...e(p),rows:e(p).rows.map(r=>({panels:r.panels.map(l=>l.panel_id!==n?l:{...l,final_col_span:a??l.inference_result.col_span})}))},!0)}function Ie(n,a){e(p)&&v(p,{...e(p),rows:e(p).rows.map(r=>({panels:r.panels.map(l=>l.panel_id!==n?l:{...l,inference_result:{...l.inference_result,panel_height_px:a??l.inference_result.panel_height_px}})}))},!0)}async function _e(n,a){const r=[...e(w)];let l=!1;for(let $=0;$<e(w).length;$++){const I=e(w)[$].inference_result.filter_controls.flatMap(me=>me.variable.split(",").map(He=>He.trim()));if(!I.includes(n)||!I.every(me=>{const He=a[me];return He!==void 0&&He!==""&&He!==null}))continue;const lt=Object.fromEntries(I.map(me=>[me,a[me]])),ct=e(m)[$];try{const me=await F(`/api/v1/panels/${ct}/execute`,{variables:lt});r[$]={panel_id:ct,...me},l=!0}catch{}}if(l){v(w,r,!0);try{v(p,await Z(r),!0)}catch{}}}function De(n,a){Yt.update(r=>({...r,[n]:a})),clearTimeout(ve),ve=window.setTimeout(()=>{const r={...h(),[n]:a};_e(n,r)},350)}function ce(n,a=3500){v(Q,n,!0),clearTimeout(ye),ye=window.setTimeout(()=>{v(Q,null)},a)}var Re=Tn(),ne=B(Re),se=i(ne),xe=i(se),ht=c(i(xe),2);{var Mt=n=>{var a=mn(),r=i(a,!0);o(a),O(()=>{Ye(a,"title",e(Te).name),N(r,e(Te).name)}),g(n,a)};z(ht,n=>{e(Te)&&n(Mt)})}var Ze=c(ht,2);{var et=n=>{var a=bn(),r=i(a);Ma(r),ka(r,!0);var l=c(r,4);o(a),Zt("submit",a,$=>{$.preventDefault(),$e()}),te("keydown",r,$=>{$.key==="Escape"&&he()}),Sa(r,()=>e(x),$=>v(x,$)),te("click",l,he),g(n,a)},tt=n=>{var a=yn();O(()=>{a.disabled=e(k),Ye(a,"title",e(k)?"Wait for current run to finish":"New dashboard")}),te("click",a,()=>{v(S,!0)}),g(n,a)};z(Ze,n=>{e(S)?n(et):n(tt,-1)})}o(xe);var _t=c(xe,2),ft=i(_t);{var St=n=>{var a=wn();let r;var l=i(a);o(a),O(()=>{r=Y(a,1,"score-btn svelte-1uha8ag",null,r,{active:e(L)}),N(l,`Score${e(Ue)!=null?`: ${e(Ue)}`:""}
                    ${e(L)?"▼":"▲"}`)}),te("click",a,()=>v(L,!e(L))),g(n,a)};z(ft,n=>{_()&&n(St)})}var at=c(ft,2),nt=i(at);let We;var Ve=c(nt,2);let Ge;o(at);var Be=c(at,2),st=i(Be,!0);o(Be),o(_t),o(se);var gt=c(se,2),pt=i(gt);{var Nt=n=>{tn(n,{get items(){return e(A)},get activeId(){return e(D)},onSelect:le})};z(pt,n=>{e(Le)&&n(Nt)})}var Qe=c(pt,2),Ke=i(Qe);{var mt=n=>{Ta(n,{get controls(){return e(Oe)},get filterVals(){return h()},onChange:De})};z(Ke,n=>{e(Fe)&&n(mt)})}var bt=c(Ke,2);{var rt=n=>{var a=xn(),r=i(a),l=i(r),$=i(l);let b;var I=c($);o(l);var re=c(l,4);{var lt=qe=>{var ze=$n(),yt=c(i(ze),2),sa=i(yt,!0);o(yt),o(ze),O(()=>{Ye(ze,"title",e(R)),N(sa,e(R))}),g(qe,ze)},ct=qe=>{var ze=kn(),yt=i(ze,!0);o(ze),O(()=>N(yt,e(T))),g(qe,ze)};z(re,qe=>{e(R)?qe(lt):e(k)&&e(T)&&e(we)&&qe(ct,1)})}o(r);var me=c(r,2),He=i(me);pn(He,{onRun:j,get disabled(){return e(k)},get theme(){return e(q)},get value(){return e(d)},set value(qe){v(d,qe,!0)}}),o(me),o(a),O(()=>{l.disabled=e(k),b=Y($,1,"run-icon svelte-1uha8ag",null,b,{spinning:e(k)}),N(I,` ${(e(k)?e(T)??"Running…":"Run")??""}`)}),te("click",l,j),g(n,a)};z(bt,n=>{_()&&n(rt)})}var ot=c(bt,2);let it;var Tt=i(ot);{var C=n=>{var a=Cn(),r=c(i(a),2),l=i(r,!0);o(r),o(a),O(()=>N(l,e(T)??"Executing…")),g(n,a)},P=n=>{var a=Sn(),r=c(i(a),2),l=i(r,!0);o(r);var $=c(r,2);{var b=I=>{var re=Mn();g(I,re)};z($,I=>{_()&&I(b)})}o(a),O(()=>N(l,_()?"Press Ctrl+Enter to run and see results here":"Switch to Edit mode to write SQL and create panels")),g(n,a)},U=n=>{Ea(n,{get layout(){return e(p)},onEditSQL:pe,onExplain:Ee,onDelete:ge,onChartOverride:Pe,onWidthOverride:ke,onHeightOverride:Ie})};z(Tt,n=>{e(k)&&!e(we)?n(C):e(we)?e(p)&&n(U,2):n(P,1)})}o(ot),o(Qe);var fe=c(Qe,2);{var K=n=>{Fa(n,{get layout(){return e(p)},onClose:()=>v(L,!1)})};z(fe,n=>{_()&&e(L)&&e(p)&&n(K)})}o(gt),o(ne);var W=c(ne,2);{var ee=n=>{var a=Nn(),r=i(a,!0);o(a),O(()=>N(r,e(Q))),g(n,a)};z(W,n=>{e(Q)&&n(ee)})}var de=c(W,2);_n(de,{}),O(()=>{We=Y(nt,1,"mode-btn svelte-1uha8ag",null,We,{active:!_()}),Ge=Y(Ve,1,"mode-btn svelte-1uha8ag",null,Ge,{active:_()}),Ye(Be,"aria-label",e(q)==="dark"?"Switch to light mode":"Switch to dark mode"),Ye(Be,"title",e(q)==="dark"?"Light mode":"Dark mode"),N(st,e(q)==="dark"?"☀":"☾"),it=Y(ot,1,"dashboard-area svelte-1uha8ag",null,it,{empty:!e(we)&&!e(k)})}),te("click",nt,()=>wt.set(!1)),te("click",Ve,()=>wt.set(!0)),te("click",Be,H),g(f,Re),Xe(),s()}Ct(["keydown","click"]);export{Hn as component};
