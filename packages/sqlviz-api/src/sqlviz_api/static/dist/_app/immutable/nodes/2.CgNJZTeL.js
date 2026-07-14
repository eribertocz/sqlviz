const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["../chunks/ekk7sIKj.js","../chunks/CXyBGMYu.js","../chunks/C0jHkEur.js","../chunks/Cea5cxJJ.js","../assets/editor.B8tIeeJt.css"])))=>i.map(i=>d[i]);
import{b as ra,a as g,f as x,c as X,d as oa}from"../chunks/EVBMHDXH.js";import{w as At,o as Jt,a as ia}from"../chunks/DxICD3qh.js";import{h as Ce,i as Rt,e as Et,b5 as la,b as ca,E as da,ab as va,f as ua,c as ha,s as Bt,d as Pt,S as _a,L as fa,b6 as ga,P as pa,al as ma,aj as dt,b7 as Ht,R as It,b8 as ba,w as e,b9 as je,a3 as ya,t as Ye,F as G,G as it,z as i,y as c,B as r,x as Je,K as W,I as O,v as B,ba as Xt,D as v,bb as wa,bc as $a,a4 as xe,u as ka}from"../chunks/C0jHkEur.js";import{f as xa,a as xt,d as te,s as N,e as Zt}from"../chunks/CY52XHtr.js";import{l as J,p as Se,s as re,a as ea,c as $t,b as Ca}from"../chunks/ds6XAry9.js";import{i as z}from"../chunks/DfobnKYw.js";import{s as Y,a as kt,c as jt,d as lt,r as Ma,b as Sa}from"../chunks/DL6DCHt6.js";import{g as Na}from"../chunks/C3xFqJt-.js";import{a as Ae,i as ct,e as yt,F as Ta,D as Ea}from"../chunks/D9jE4LIp.js";import{c as Pa,_ as Da}from"../chunks/CXyBGMYu.js";import{B as La}from"../chunks/Cea5cxJJ.js";function ae(f,t,u,h,_){var d;Ce&&Rt();var b=(d=t.$$slots)==null?void 0:d[u],s=!1;b===!0&&(b=t.children,s=!0),b===void 0||b(f,s?()=>h:h)}function Ra(f,t,u,h,_,b){let s=Ce;Ce&&Rt();var d=null;Ce&&Et.nodeType===la&&(d=Et,Rt());var p=Ce?Et:f,C=new La(p,!1);ca(()=>{const T=t()||null;var R=ga;if(T===null){C.ensure(null,null);return}return C.ensure(T,I=>{if(T){if(d=Ce?d:va(T,R),ra(d,d),h){var H=null;Ce&&xa(T)&&d.append(H=document.createComment(""));var D=Ce?ua(d):d.appendChild(ha());Ce&&(D===null?Bt(!1):Pt(D)),h(d,D),H==null||H.remove()}_a.nodes.end=d,I.before(d)}Ce&&Pt(I)}),()=>{}},da),fa(()=>{}),s&&(Bt(!0),Pt(p))}function ta(f=!1){const t=pa,u=t.l.u;if(!u)return;let h=()=>je(t.s);if(f){let _=0,b={};const s=ya(()=>{let d=!1;const p=t.s;for(const C in p)p[C]!==b[C]&&(b[C]=p[C],d=!0);return d&&_++,_});h=()=>e(s)}u.b.length&&ma(()=>{Ut(t,h),Ht(u.b)}),dt(()=>{const _=It(()=>u.m.map(ba));return()=>{for(const b of _)typeof b=="function"&&b()}}),u.a.length&&dt(()=>{Ut(t,h),Ht(u.a)})}function Ut(f,t){if(f.l.s)for(const u of f.l.s)e(u);t()}var Ia=x('<div class="no-data svelte-7vbfso"><p class="svelte-7vbfso">Score available after dashboard execution.</p> <p class="hint svelte-7vbfso">V0.2 backend required for utility scoring.</p></div>'),qa=x('<span class="low-good-hint svelte-7vbfso">(low=good)</span>'),za=x('<div class="breakdown-row svelte-7vbfso"><span class="dim-name svelte-7vbfso"> </span> <div class="mini-track svelte-7vbfso"><div class="mini-fill svelte-7vbfso"></div></div> <span> <!></span></div>'),Aa=x('<div class="breakdown-block svelte-7vbfso"></div>'),Oa=x('<button class="action-btn apply svelte-7vbfso">Apply</button>'),Ba=x('<div class="suggestion svelte-7vbfso"><div class="suggestion-text svelte-7vbfso"><span class="warn-icon svelte-7vbfso">⚠</span> <div><strong> </strong> <span class="suggestion-body svelte-7vbfso"> </span> <span class="impact svelte-7vbfso"> </span></div></div> <div class="suggestion-actions svelte-7vbfso"><!> <button class="action-btn dismiss svelte-7vbfso">Dismiss</button></div></div>'),Ha=x('<div class="suggestions-block svelte-7vbfso"><span class="suggestions-label svelte-7vbfso">Sugerencias</span> <!></div>'),ja=x('<div class="utility-block svelte-7vbfso"><div class="score-row svelte-7vbfso"><span class="score-heading svelte-7vbfso">Utility Score</span> <span> </span></div> <div class="score-track svelte-7vbfso"><div class="score-fill svelte-7vbfso"></div></div></div> <!> <!>',1),Ua=x('<aside class="score-panel svelte-7vbfso" aria-label="Dashboard Score"><div class="panel-header svelte-7vbfso"><span class="panel-title svelte-7vbfso">Dashboard Score</span> <button class="close-btn svelte-7vbfso" aria-label="Close score panel">×</button></div> <!></aside>');function Fa(f,t){Ye(t,!0);function u(y){return y>=85?{text:"Excellent",cls:"excellent"}:y>=70?{text:"Good",cls:"good"}:y>=55?{text:"Fair",cls:"fair"}:{text:"Needs work",cls:"needs-work"}}const h=W(()=>Math.round((t.layout.utility_score??0)*100)),_=W(()=>u(e(h))),b=W(()=>(t.layout.suggestions??[]).slice().sort((y,L)=>L.score_impact-y.score_impact)),s=W(()=>t.layout.utility_breakdown??{}),d=W(()=>t.layout.utility_score!=null);let p=G(it(new Set));const C=W(()=>e(b).filter(y=>!e(p).has(y.panel_id+y.suggestion)));function T(y){v(p,new Set([...e(p),y.panel_id+y.suggestion]),!0)}var R=Ua(),I=i(R),H=c(i(I),2);r(I);var D=c(I,2);{var m=y=>{var L=Ia();g(y,L)},E=y=>{var L=ja(),A=O(L),S=i(A),$=c(i(S),2),Q=i($);r($),r(S);var be=c(S,2),ye=i(be);r(be),r(A);var Le=c(A,2);{var Ne=de=>{var F=Aa();Ae(F,21,()=>Object.entries(e(s)),([ve,Z])=>ve,(ve,Z)=>{var j=W(()=>Xt(e(Z),2));let fe=()=>e(j)[0],ge=()=>e(j)[1];const Te=W(()=>Math.round(Number(ge())*100)),we=W(()=>fe()==="cognitive_load"||fe()==="space_waste");var ue=za(),ie=i(ue),Ee=i(ie,!0);r(ie);var $e=c(ie,2),Re=i($e);r($e);var he=c($e,2);let Pe;var le=i(he),Ie=c(le);{var ne=se=>{var ke=qa();g(se,ke)};z(Ie,se=>{e(we)&&se(ne)})}r(he),r(ue),B(se=>{N(Ee,fe()),kt(Re,`width: ${e(Te)??""}%`),Pe=Y(he,1,"dim-value svelte-7vbfso",null,Pe,{"low-good":e(we)}),N(le,`${se??""} `)},[()=>Number(ge()).toFixed(2)]),g(ve,ue)}),r(F),g(de,F)},Ue=W(()=>Object.keys(e(s)).length>0);z(Le,de=>{e(Ue)&&de(Ne)})}var Oe=c(Le,2);{var Fe=de=>{var F=Ha(),ve=c(i(F),2);Ae(ve,17,()=>e(C),Z=>Z.panel_id+Z.suggestion,(Z,j)=>{var fe=Ba(),ge=i(fe),Te=c(i(ge),2),we=i(Te),ue=i(we,!0);r(we);var ie=c(we,2),Ee=i(ie);r(ie);var $e=c(ie,2),Re=i($e);r($e),r(Te),r(ge);var he=c(ge,2),Pe=i(he);{var le=ne=>{var se=Oa();te("click",se,()=>{var ke;return(ke=t.onApplySuggestion)==null?void 0:ke.call(t,e(j).panel_id,e(j).action)}),g(ne,se)};z(Pe,ne=>{e(j).action&&t.onApplySuggestion&&ne(le)})}var Ie=c(Pe,2);r(he),r(fe),B(ne=>{N(ue,e(j).panel_label??e(j).panel_id),N(Ee,`— ${e(j).suggestion??""}`),N(Re,`(+${ne??""}% utility)`)},[()=>Math.round(e(j).score_impact*100)]),te("click",Ie,()=>T(e(j))),g(Z,fe)}),r(F),g(de,F)};z(Oe,de=>{e(C).length>0&&de(Fe)})}B(()=>{Y($,1,`score-value ${e(_).cls??""}`,"svelte-7vbfso"),N(Q,`${e(h)??""} / 100 · ${e(_).text??""}`),kt(ye,`width: ${e(h)??""}%`)}),g(y,L)};z(D,y=>{e(d)?y(E,-1):y(m)})}r(R),te("click",H,function(...y){var L;(L=t.onClose)==null||L.apply(this,y)}),g(f,R),Je()}xt(["click"]);wa();/**
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
 */const Va={xmlns:"http://www.w3.org/2000/svg",width:24,height:24,viewBox:"0 0 24 24",fill:"none",stroke:"currentColor","stroke-width":2,"stroke-linecap":"round","stroke-linejoin":"round"};/**
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
 */const Wa=f=>{for(const t in f)if(t.startsWith("aria-")||t==="role"||t==="title")return!0;return!1};/**
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
 */const Ft=(...f)=>f.filter((t,u,h)=>!!t&&t.trim()!==""&&h.indexOf(t)===u).join(" ").trim();var Ga=oa("<svg><!><!></svg>");function oe(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]),h=J(u,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);Ye(t,!1);let _=Se(t,"name",8,void 0),b=Se(t,"color",8,"currentColor"),s=Se(t,"size",8,24),d=Se(t,"strokeWidth",8,2),p=Se(t,"absoluteStrokeWidth",8,!1),C=Se(t,"iconNode",24,()=>[]);ta();var T=Ga();jt(T,(H,D,m)=>({...Va,...H,...h,width:s(),height:s(),stroke:b(),"stroke-width":D,class:m}),[()=>Wa(h)?void 0:{"aria-hidden":"true"},()=>(je(p()),je(d()),je(s()),It(()=>p()?Number(d())*24/Number(s()):d())),()=>(je(Ft),je(_()),je(u),It(()=>Ft("lucide-icon","lucide",_()?`lucide-${_()}`:"",u.class)))]);var R=i(T);Ae(R,1,C,ct,(H,D)=>{var m=W(()=>Xt(e(D),2));let E=()=>e(m)[0],y=()=>e(m)[1];var L=X(),A=O(L);Ra(A,E,!0,(S,$)=>{jt(S,()=>({...y()}))}),g(H,L)});var I=c(R);ae(I,t,"default",{}),r(T),g(f,T),Je()}function aa(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["path",{d:"M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"}]];oe(f,re({name:"activity"},()=>u,{get iconNode(){return h},children:(_,b)=>{var s=X(),d=O(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function Qa(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"M7 11h8"}],["path",{d:"M7 16h3"}],["path",{d:"M7 6h12"}]];oe(f,re({name:"chart-bar-decreasing"},()=>u,{get iconNode(){return h},children:(_,b)=>{var s=X(),d=O(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function wt(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"M7 16h8"}],["path",{d:"M7 11h12"}],["path",{d:"M7 6h3"}]];oe(f,re({name:"chart-bar"},()=>u,{get iconNode(){return h},children:(_,b)=>{var s=X(),d=O(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function na(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"m19 9-5 5-4-4-3 3"}]];oe(f,re({name:"chart-line"},()=>u,{get iconNode(){return h},children:(_,b)=>{var s=X(),d=O(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function Ka(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["path",{d:"M21 12c.552 0 1.005-.449.95-.998a10 10 0 0 0-8.953-8.951c-.55-.055-.998.398-.998.95v8a1 1 0 0 0 1 1z"}],["path",{d:"M21.21 15.89A10 10 0 1 1 8 2.83"}]];oe(f,re({name:"chart-pie"},()=>u,{get iconNode(){return h},children:(_,b)=>{var s=X(),d=O(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function Ya(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["circle",{cx:"7.5",cy:"7.5",r:".5",fill:"currentColor"}],["circle",{cx:"18.5",cy:"5.5",r:".5",fill:"currentColor"}],["circle",{cx:"11.5",cy:"11.5",r:".5",fill:"currentColor"}],["circle",{cx:"7.5",cy:"16.5",r:".5",fill:"currentColor"}],["circle",{cx:"17.5",cy:"14.5",r:".5",fill:"currentColor"}],["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}]];oe(f,re({name:"chart-scatter"},()=>u,{get iconNode(){return h},children:(_,b)=>{var s=X(),d=O(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function Dt(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["line",{x1:"4",x2:"20",y1:"9",y2:"9"}],["line",{x1:"4",x2:"20",y1:"15",y2:"15"}],["line",{x1:"10",x2:"8",y1:"3",y2:"21"}],["line",{x1:"16",x2:"14",y1:"3",y2:"21"}]];oe(f,re({name:"hash"},()=>u,{get iconNode(){return h},children:(_,b)=>{var s=X(),d=O(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function Ot(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["rect",{width:"7",height:"9",x:"3",y:"3",rx:"1"}],["rect",{width:"7",height:"5",x:"14",y:"3",rx:"1"}],["rect",{width:"7",height:"9",x:"14",y:"12",rx:"1"}],["rect",{width:"7",height:"5",x:"3",y:"16",rx:"1"}]];oe(f,re({name:"layout-dashboard"},()=>u,{get iconNode(){return h},children:(_,b)=>{var s=X(),d=O(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function Vt(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["path",{d:"M2 5h20"}],["path",{d:"M6 12h12"}],["path",{d:"M9 19h6"}]];oe(f,re({name:"list-filter"},()=>u,{get iconNode(){return h},children:(_,b)=>{var s=X(),d=O(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function Ja(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["path",{d:"M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"}]];oe(f,re({name:"table-2"},()=>u,{get iconNode(){return h},children:(_,b)=>{var s=X(),d=O(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function me(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["path",{d:"M16 7h6v6"}],["path",{d:"m22 7-8.5 8.5-5-5L2 17"}]];oe(f,re({name:"trending-up"},()=>u,{get iconNode(){return h},children:(_,b)=>{var s=X(),d=O(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function Lt(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]];oe(f,re({name:"triangle-alert"},()=>u,{get iconNode(){return h},children:(_,b)=>{var s=X(),d=O(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function Wt(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["path",{d:"M10 14.66v1.626a2 2 0 0 1-.976 1.696A5 5 0 0 0 7 21.978"}],["path",{d:"M14 14.66v1.626a2 2 0 0 0 .976 1.696A5 5 0 0 1 17 21.978"}],["path",{d:"M18 9h1.5a1 1 0 0 0 0-5H18"}],["path",{d:"M4 22h16"}],["path",{d:"M6 9a6 6 0 0 0 12 0V3a1 1 0 0 0-1-1H7a1 1 0 0 0-1 1z"}],["path",{d:"M6 9H4.5a1 1 0 0 1 0-5H6"}]];oe(f,re({name:"trophy"},()=>u,{get iconNode(){return h},children:(_,b)=>{var s=X(),d=O(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}function Me(f,t){const u=J(t,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["path",{d:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"}],["path",{d:"M16 3.128a4 4 0 0 1 0 7.744"}],["path",{d:"M22 21v-2a4 4 0 0 0-3-3.87"}],["circle",{cx:"9",cy:"7",r:"4"}]];oe(f,re({name:"users"},()=>u,{get iconNode(){return h},children:(_,b)=>{var s=X(),d=O(s);ae(d,t,"default",{}),g(_,s)},$$slots:{default:!0}}))}const Gt={kpi_overview:Dt,kpi_performance:me,financial_kpi:Dt,sales_kpi:Dt,hr_overview:Me,trend_analysis:me,financial_trend:me,product_growth:me,sales_performance:me,marketing_performance:me,hr_trend:me,ops_monitoring:aa,user_lifecycle:Me,user_retention:Me,retention_analysis:Me,cohort_analysis:Me,product_retention:Me,funnel_analysis:Vt,product_funnel:Vt,financial_dashboard:me,financial_comparison:wt,sales_dashboard:me,sales_ranking:Wt,marketing_analytics:na,marketing_comparison:wt,product_analytics:Me,hr_analytics:Me,comparison_analysis:wt,competitive_analysis:wt,ranking_analysis:Wt,distribution_analysis:Qa,correlation_analysis:Ya,composition_analysis:Ka,anomaly_detection:Lt,anomaly_monitoring:Lt,incident_monitoring:Lt,data_detail:Ja,analytics_overview:Ot},Qt={finance:me,product:Me,marketing:na,hr:Me,ops:aa,sales:me,analytics:Ot};function Xa(f,t,u){return f&&Gt[f]?Gt[f]:t&&Qt[t]?Qt[t]:Ot}var Za=x('<li><button><span class="panel-icon svelte-609rsk"><!></span> <span class="panel-title svelte-609rsk"> </span></button></li>'),en=x('<nav class="dashboard-sidebar svelte-609rsk" aria-label="Dashboard navigation"><div class="sidebar-label svelte-609rsk">Dashboards</div> <ul class="panel-list svelte-609rsk"></ul></nav>');function tn(f,t){Ye(t,!0);let u=Se(t,"activeId",3,null);var h=en(),_=c(i(h),2);Ae(_,21,()=>t.items,b=>b.id,(b,s)=>{const d=W(()=>Xa(e(s).dashboard_hint,e(s).dashboard_domain));var p=Za(),C=i(p);let T;var R=i(C),I=i(R);Pa(I,()=>e(d),(m,E)=>{E(m,{size:14})}),r(R);var H=c(R,2),D=i(H,!0);r(H),r(C),r(p),B(()=>{T=Y(C,1,"panel-item svelte-609rsk",null,T,{active:e(s).id===u()}),lt(C,"title",e(s).name),N(D,e(s).name)}),te("click",C,()=>{var m;return(m=t.onSelect)==null?void 0:m.call(t,e(s).id)}),g(b,p)}),r(_),r(h),g(f,h),Je()}xt(["click"]);const qt=At(null);var an=x('<div class="banner fallback svelte-10vh4gh"><span class="banner-icon svelte-10vh4gh">⚠</span> <div><strong class="svelte-10vh4gh">Inference without data</strong> <p class="svelte-10vh4gh"> </p></div></div>'),nn=x('<div class="intent-desc svelte-10vh4gh"> </div>'),sn=x('<li class="signal-item svelte-10vh4gh"><span class="signal-dot svelte-10vh4gh">✓</span> <span class="signal-name svelte-10vh4gh"> </span> <span class="signal-score svelte-10vh4gh"> </span></li>'),rn=x('<div class="subsection-title svelte-10vh4gh">Key signals</div> <ul class="signal-list svelte-10vh4gh"></ul>',1),on=x('<p class="muted-note svelte-10vh4gh">Signal data unavailable — run the panel to see details.</p>'),Kt=x('<div class="score-row svelte-10vh4gh"><span> </span> <div class="bar-track svelte-10vh4gh"><div></div></div> <span> </span></div>'),ln=x('<div class="subsection-title svelte-10vh4gh">Intent scores</div> <div class="score-bars svelte-10vh4gh"></div>',1),cn=x('<p class="chart-desc svelte-10vh4gh"> </p>'),dn=x('<div class="subsection-title svelte-10vh4gh">Chart scores</div> <div class="score-bars svelte-10vh4gh"></div>',1),vn=x('<li class="error-item svelte-10vh4gh"> </li>'),un=x('<div class="subsection-title svelte-10vh4gh">Errors</div> <ul class="error-list svelte-10vh4gh"></ul>',1),hn=x('<div class="backdrop svelte-10vh4gh" role="presentation"></div> <aside class="explain-drawer svelte-10vh4gh" aria-label="Explainability panel"><div class="drawer-header svelte-10vh4gh"><h2 class="drawer-title svelte-10vh4gh">Why this chart?</h2> <button class="close-btn svelte-10vh4gh" aria-label="Close">✕</button></div> <div class="drawer-body svelte-10vh4gh"><!> <section class="section svelte-10vh4gh"><h3 class="section-title svelte-10vh4gh">Detected intent</h3> <div class="intent-badge svelte-10vh4gh"><span class="intent-icon svelte-10vh4gh"> </span> <div><div class="intent-name svelte-10vh4gh"> </div> <!></div></div> <!> <!></section> <section class="section svelte-10vh4gh"><h3 class="section-title svelte-10vh4gh">Selected chart</h3> <div class="chart-badge svelte-10vh4gh"><strong class="svelte-10vh4gh"> </strong> <!></div> <!></section> <section class="section svelte-10vh4gh"><h3 class="section-title svelte-10vh4gh">Inference confidence</h3> <div class="quality-row svelte-10vh4gh"><span> </span></div> <p class="quality-detail svelte-10vh4gh"> </p> <!></section> <div class="debug-row svelte-10vh4gh"><span class="debug-item svelte-10vh4gh">fingerprint: <code class="svelte-10vh4gh"> </code></span> <span class="debug-item svelte-10vh4gh"> </span> <span class="debug-item svelte-10vh4gh"> </span></div></div></aside>',1);function _n(f,t){Ye(t,!1);const u=()=>$t(qt,"$explainTarget",h),[h,_]=ea(),b={has_group_by:"Groups results with GROUP BY",has_order_by:"Results are ordered sequentially",has_order_by_desc:"Results ordered descending (ranking)",has_limit:"Uses TOP/LIMIT (top-N records)",has_aggregation:"Uses aggregation (SUM, COUNT, AVG…)",has_sum:"Uses SUM aggregate",has_count:"Uses COUNT aggregate",has_avg:"Uses AVG aggregate",has_window_function:"Window function (RANK, ROW_NUMBER…)",has_cte:"Uses Common Table Expression (WITH…)",has_join:"Joins multiple tables",has_where:"Filters data with WHERE",has_date_column:"Contains a date/time column",has_numeric_column:"Contains numeric columns",has_string_column:"Contains text/string columns",has_single_numeric_column:"Returns a single numeric value",has_two_numeric_columns:"Returns two numeric columns (x/y pair)",has_temporal_dimension:"Temporal grouping (date/time)",has_geographic_dimension:"Geographic grouping (location)",has_revenue_metric:"Revenue or monetary metric detected",has_product_entity:"Product or item entity detected",has_customer_entity:"Customer or user entity detected",has_distinct:"Uses DISTINCT",has_case_when:"Contains CASE WHEN logic",has_outliers:"Data contains statistical outliers",has_outliers_detected:"Outlier values detected in results",has_partition_by:"Uses PARTITION BY",has_subquery:"Contains a subquery",result_row_count_is_1:"Returns exactly 1 row (single metric)",result_column_count_is_1:"Returns exactly 1 column",result_is_wide_table:"Wide table — many columns, general data",numeric_column_ratio:"High proportion of numeric columns",date_column_ratio:"High proportion of date columns",row_count_normalized:"Number of result rows (non-zero)",cardinality_ratio:"Category uniqueness ratio",temporal_cardinality:"Distinct time periods in result",trend_strength:"Statistical trend detected in values",no_group_by:"No GROUP BY clause",no_aggregation:"No aggregate functions",no_temporal_dimension:"No temporal dimension present",no_order_by_desc:"Not ordered descending",no_numeric_column:"No numeric output columns",no_case_when:"No conditional logic",no_customer_entity:"No customer entity found",no_count:"No COUNT aggregate",order_desc_and_limit:"Top-N ranking pattern (DESC + LIMIT)",high_cardinality:"Many unique categories",low_cardinality:"Few distinct categories",multiple_rows:"Returns multiple rows",single_numeric_column:"Single numeric column in result",high_col_count:"Many columns selected",group_by_count_gte_2:"Groups by 2 or more dimensions",part_of_whole_score:"Part-of-whole pattern (share/percentage)",is_monotonic_decreasing:"Values consistently decrease (funnel)",distinct_entity_count_over_time:"Distinct users counted over time (retention)",has_percentile:"Uses percentile/quantile function"},s={trend:{label:"Temporal Trend",icon:"↗",description:"Values change over time. The SQL groups by a date or sequential column with an ORDER BY."},comparison:{label:"Comparison",icon:"⇄",description:"Values compared across distinct categories such as products, regions or segments."},kpi:{label:"Key Metric (KPI)",icon:"#",description:"A single aggregate number — the SQL returns one summary value with no GROUP BY."},distribution:{label:"Distribution",icon:"∿",description:"How values are spread across a range or bucket (histogram-style data)."},geospatial:{label:"Geographic",icon:"⊕",description:"Data has a geographic dimension such as country, region or coordinates."},relationship:{label:"Correlation",icon:"◎",description:"Two numeric dimensions that may be correlated — scatter-plot pattern."},composition:{label:"Composition",icon:"◔",description:"Parts that add up to a whole — market share, budget split, category breakdown."},retention:{label:"Retention / Cohort",icon:"⟲",description:"Tracks how many users or customers return over time (COUNT DISTINCT over temporal)."},funnel:{label:"Funnel",icon:"▽",description:"Sequential steps where values consistently decrease — conversion or drop-off."},ranking:{label:"Ranking / Top-N",icon:"▲",description:"Top values sorted descending with a LIMIT — leaderboard or best performers."},detail:{label:"Tabular Detail",icon:"≡",description:"General table of records with no clear analytical pattern."},anomaly:{label:"Anomaly Detection",icon:"!",description:"Highlights outlier or unusual values in the data."}},d={line:{label:"Line Chart",description:"Shows how a value evolves over time or a sequential dimension."},bar:{label:"Bar Chart",description:"Compares discrete values across categories side by side."},bar_horizontal:{label:"Horizontal Bar",description:"Same as bar but rotated — better when category labels are long."},pie:{label:"Pie Chart",description:"Shows each category as a fraction of the total."},scatter:{label:"Scatter Plot",description:"Reveals correlations between two numeric variables."},histogram:{label:"Histogram",description:"Distribution of a single numeric variable across value buckets."},table:{label:"Table",description:"Presents all records when no single visualization fits better."},kpi:{label:"KPI Card",description:"A single headline number — the most important metric, front and center."}},p={high:{label:"High confidence",cls:"positive",detail:"The SQL pattern clearly matches the detected intent. This visualization is highly reliable."},medium:{label:"Medium confidence",cls:"neutral",detail:"The SQL pattern partially matches. The result is likely correct but some ambiguity exists."},low:{label:"Low confidence",cls:"negative",detail:"The SQL pattern is ambiguous. Consider rephrasing your query for clearer inference."}};function C(S){return S.explanation.filter($=>$.contribution>0).sort(($,Q)=>Q.contribution-$.contribution).slice(0,5)}function T(S){return b[S]??S.replace(/_/g," ")}function R(S){return s[S]??{label:S,icon:"?",description:""}}function I(S){return d[S]??{label:S,description:""}}function H(S){return p[S]??p.low}function D(S,$){return $===0?"4%":Math.max(4,Math.round(S/$*100))+"%"}function m(){qt.set(null)}function E(S){S.key==="Escape"&&m()}ta();var y=X();Zt("keydown",$a,E);var L=O(y);{var A=S=>{const $=xe(()=>u().inference_result),Q=xe(()=>C(e($))),be=xe(()=>R(e($).intent_winner)),ye=xe(()=>I(e($).chart_winner)),Le=xe(()=>H(e($).chart_quality)),Ne=xe(()=>[{intent:e($).intent_winner,raw_score:e($).intent_raw_score},...e($).intent_alternatives]),Ue=xe(()=>Math.max(...e(Ne).map(k=>k.raw_score),.01)),Oe=xe(()=>e($).chart_alternatives),Fe=xe(()=>[{chart:e($).chart_winner,raw_score:e($).chart_raw_score},...e(Oe)]),de=xe(()=>Math.max(...e(Fe).map(k=>k.raw_score),.01));var F=hn(),ve=O(F),Z=c(ve,2),j=i(Z),fe=c(i(j),2);r(j);var ge=c(j,2),Te=i(ge);{var we=k=>{var P=an(),U=c(i(P),2),_e=c(i(U),2),K=i(_e,!0);r(_e),r(U),r(P),B(()=>N(K,e($).fallback_reason||"The query could not be executed, so inference ran on SQL structure only.")),g(k,P)};z(Te,k=>{e($).fallback_applied&&k(we)})}var ue=c(Te,2),ie=c(i(ue),2),Ee=i(ie),$e=i(Ee,!0);r(Ee);var Re=c(Ee,2),he=i(Re),Pe=i(he,!0);r(he);var le=c(he,2);{var Ie=k=>{var P=nn(),U=i(P,!0);r(P),B(()=>N(U,e(be).description)),g(k,P)};z(le,k=>{e(be).description&&k(Ie)})}r(Re),r(ie);var ne=c(ie,2);{var se=k=>{var P=rn(),U=c(O(P),2);Ae(U,5,()=>e(Q),ct,(_e,K)=>{var V=sn(),ee=c(i(V),2),ce=i(ee,!0);r(ee);var n=c(ee,2),a=i(n,!0);r(n),r(V),B((o,l)=>{N(ce,o),N(a,l)},[()=>T(e(K).signal),()=>e(K).contribution.toFixed(2)]),g(_e,V)}),r(U),g(k,P)},ke=k=>{var P=on();g(k,P)};z(ne,k=>{e(Q).length>0?k(se):k(ke,-1)})}var vt=c(ne,2);{var Ct=k=>{var P=ln(),U=c(O(P),2);Ae(U,5,()=>e(Ne),ct,(_e,K,V)=>{var ee=Kt(),ce=i(ee);Y(ce,1,"score-label svelte-10vh4gh",null,{},{winner:V===0});var n=i(ce,!0);r(ce);var a=c(ce,2),o=i(a);Y(o,1,"bar-fill svelte-10vh4gh",null,{},{"bar-winner":V===0}),r(a);var l=c(a,2);Y(l,1,"score-value svelte-10vh4gh",null,{},{winner:V===0});var w=i(l,!0);r(l),r(ee),B((M,q,De)=>{N(n,M),kt(o,`width: ${q??""}`),N(w,De)},[()=>R(e(K).intent).label,()=>D(e(K).raw_score,e(Ue)),()=>e(K).raw_score.toFixed(2)]),g(_e,ee)}),r(U),g(k,P)};z(vt,k=>{e(Ne).length>1&&k(Ct)})}r(ue);var Xe=c(ue,2),Ze=c(i(Xe),2),et=i(Ze),ut=i(et,!0);r(et);var ht=c(et,2);{var Mt=k=>{var P=cn(),U=i(P,!0);r(P),B(()=>N(U,e(ye).description)),g(k,P)};z(ht,k=>{e(ye).description&&k(Mt)})}r(Ze);var tt=c(Ze,2);{var at=k=>{var P=dn(),U=c(O(P),2);Ae(U,5,()=>e(Fe),ct,(_e,K,V)=>{var ee=Kt(),ce=i(ee);Y(ce,1,"score-label svelte-10vh4gh",null,{},{winner:V===0});var n=i(ce,!0);r(ce);var a=c(ce,2),o=i(a);Y(o,1,"bar-fill svelte-10vh4gh",null,{},{"bar-winner":V===0}),r(a);var l=c(a,2);Y(l,1,"score-value svelte-10vh4gh",null,{},{winner:V===0});var w=i(l,!0);r(l),r(ee),B((M,q,De)=>{N(n,M),kt(o,`width: ${q??""}`),N(w,De)},[()=>I(e(K).chart).label,()=>D(e(K).raw_score,e(de)),()=>e(K).raw_score.toFixed(2)]),g(_e,ee)}),r(U),g(k,P)};z(tt,k=>{e(Oe).length>0&&k(at)})}r(Xe);var Ve=c(Xe,2),We=c(i(Ve),2),Ge=i(We),Be=i(Ge,!0);r(Ge),r(We);var nt=c(We,2),_t=i(nt,!0);r(nt);var ft=c(nt,2);{var St=k=>{var P=un(),U=c(O(P),2);Ae(U,5,()=>e($).errors,ct,(_e,K)=>{var V=vn(),ee=i(V,!0);r(V),B(()=>N(ee,e(K))),g(_e,V)}),r(U),g(k,P)};z(ft,k=>{e($).errors.length>0&&k(St)})}r(Ve);var Qe=c(Ve,2),Ke=i(Qe),gt=c(i(Ke)),pt=i(gt);r(gt),r(Ke);var st=c(Ke,2),rt=i(st,!0);r(st);var ot=c(st,2),Nt=i(ot);r(ot),r(Qe),r(ge),r(Z),B((k,P)=>{N($e,e(be).icon),N(Pe,e(be).label),N(ut,e(ye).label),Y(Ge,1,`quality-badge ${e(Le).cls??""}`,"svelte-10vh4gh"),N(Be,e(Le).label),N(_t,e(Le).detail),N(pt,`${k??""}…`),N(rt,e($).engine_version),N(Nt,`${P??""} ms`)},[()=>e($).fingerprint.slice(0,12),()=>e($).elapsed_ms.toFixed(1)]),te("click",ve,m),te("keydown",ve,()=>{}),te("click",fe,m),g(S,F)};z(L,S=>{u()&&S(A)})}g(f,y),Je(),_()}xt(["click","keydown"]);const zt=At({});var fn=x('<div class="editor-loading svelte-1dhf0v9">Loading editor…</div>'),gn=x('<div class="editor-host svelte-1dhf0v9"><!> <div></div></div>');function pn(f,t){Ye(t,!0);let u=Se(t,"value",15,""),h=Se(t,"disabled",3,!1),_=Se(t,"theme",3,"dark"),b,s=null,d=null,p=G(!1),C=!1;Jt(async()=>{window.MonacoEnvironment||(window.MonacoEnvironment={getWorker(m,E){return new Worker(URL.createObjectURL(new Blob(["self.onmessage=function(){}"],{type:"text/javascript"})))}});try{const m=await Da(()=>import("../chunks/ekk7sIKj.js").then(E=>E.b),__vite__mapDeps([0,1,2,3,4]),import.meta.url);m.editor.defineTheme("sqlviz-dark",{base:"vs-dark",inherit:!0,rules:[{token:"keyword",foreground:"a78bfa"},{token:"string",foreground:"22c55e"},{token:"comment",foreground:"64748b",fontStyle:"italic"},{token:"number",foreground:"f59e0b"}],colors:{"editor.background":"#0f172a","editor.foreground":"#f1f5f9","editor.lineHighlightBackground":"#1e293b","editor.selectionBackground":"#6366f133","editorLineNumber.foreground":"#475569","editorLineNumber.activeForeground":"#94a3b8","editorCursor.foreground":"#6366f1","scrollbarSlider.background":"#334155","scrollbarSlider.hoverBackground":"#475569","editorBracketMatch.background":"#6366f120","editorBracketMatch.border":"#6366f1"}}),m.editor.defineTheme("sqlviz-light",{base:"vs",inherit:!0,rules:[{token:"keyword",foreground:"4f46e5"},{token:"string",foreground:"16a34a"},{token:"comment",foreground:"64748b",fontStyle:"italic"},{token:"number",foreground:"d97706"}],colors:{"editor.background":"#ffffff","editor.foreground":"#0f172a","editor.lineHighlightBackground":"#f8fafc","editor.selectionBackground":"#6366f133","editorLineNumber.foreground":"#94a3b8","editorLineNumber.activeForeground":"#64748b","editorCursor.foreground":"#6366f1","scrollbarSlider.background":"#e2e8f0","scrollbarSlider.hoverBackground":"#cbd5e1","editorBracketMatch.background":"#6366f120","editorBracketMatch.border":"#6366f1"}}),s=m.editor.create(b,{value:u(),language:"sql",theme:_()==="light"?"sqlviz-light":"sqlviz-dark",minimap:{enabled:!1},fontSize:13,fontFamily:"'JetBrains Mono', 'Cascadia Code', 'Fira Code', 'Consolas', monospace",lineNumbers:"on",scrollBeyondLastLine:!1,wordWrap:"off",tabSize:4,renderLineHighlight:"line",padding:{top:12,bottom:12},folding:!1,lineNumbersMinChars:3,glyphMargin:!1,overviewRulerLanes:0}),s.addCommand(m.KeyMod.CtrlCmd|m.KeyCode.Enter,()=>{var E;return(E=t.onRun)==null?void 0:E.call(t)}),s.addCommand(m.KeyMod.CtrlCmd|m.KeyCode.KeyS,()=>{var E;return(E=t.onRun)==null?void 0:E.call(t)}),s.onDidChangeModelContent(()=>{C=!0,u(s.getValue()),C=!1}),zt.set({focusStatement(E){if(!s)return;const y=s.getModel();if(!y)return;const L=s.getValue();let A=0;if(E>0){let $=0;for(let Q=0;Q<L.length;Q++)if(L[Q]===";"&&($++,$===E)){A=Q+1;break}for(;A<L.length&&(L[A]===`
`||L[A]==="\r"||L[A]===" ");)A++}const S=y.getPositionAt(A);s.revealLineInCenter(S.lineNumber),s.setPosition(S),s.focus()}}),d=m,v(p,!0),requestAnimationFrame(()=>{s==null||s.layout(),s==null||s.focus()})}catch(m){console.error("[SQLEditor] Monaco init failed:",m),v(p,!0)}}),ia(()=>{zt.set({}),s==null||s.dispose(),s=null}),dt(()=>{if(s&&!C&&s.getValue()!==u()){const m=s.getPosition();s.setValue(u()),m&&s.setPosition(m)}}),dt(()=>{s&&s.updateOptions({readOnly:h()})}),dt(()=>{!e(p)||!d||!s||d.editor.setTheme(_()==="light"?"sqlviz-light":"sqlviz-dark")});var T=gn(),R=i(T);{var I=m=>{var E=fn();g(m,E)};z(R,m=>{e(p)||m(I)})}var H=c(R,2);let D;Ca(H,m=>b=m,()=>b),r(T),B(()=>D=Y(H,1,"editor-container svelte-1dhf0v9",null,D,{hidden:!e(p)})),g(f,T),Je()}const Yt=At({});var mn=x('<span class="dash-name svelte-1uha8ag"> </span>'),bn=x('<form class="new-dash-form svelte-1uha8ag"><input class="new-dash-input svelte-1uha8ag" placeholder="Dashboard name"/> <button type="submit" class="new-dash-confirm svelte-1uha8ag">Create</button> <button type="button" class="new-dash-cancel svelte-1uha8ag">✕</button></form>'),yn=x('<button class="new-dash-btn svelte-1uha8ag" title="New dashboard">+ New</button>'),wn=x('<button title="Dashboard Score"> </button>'),$n=x('<div class="error-chip svelte-1uha8ag"><span>✕</span> <span class="error-text svelte-1uha8ag"> </span></div>'),kn=x('<span class="exec-inline svelte-1uha8ag"> </span>'),xn=x('<div class="editor-section svelte-1uha8ag"><div class="editor-toolbar svelte-1uha8ag"><button class="run-btn svelte-1uha8ag"><span>▶</span> </button> <kbd class="shortcut svelte-1uha8ag">Ctrl+Enter</kbd> <!></div> <div class="editor-wrapper svelte-1uha8ag"><!></div></div>'),Cn=x('<div class="state-msg svelte-1uha8ag"><span class="spinner svelte-1uha8ag">⟳</span> <span> </span></div>'),Mn=x('<p class="hint svelte-1uha8ag">Separate multiple queries with <code class="svelte-1uha8ag">;</code> — each becomes a panel</p>'),Sn=x('<div class="empty-state svelte-1uha8ag"><div class="empty-arrow svelte-1uha8ag">⬇</div> <p class="svelte-1uha8ag"> </p> <!></div>'),Nn=x('<div class="toast svelte-1uha8ag" role="status" aria-live="polite"> </div>'),Tn=x('<div class="app-shell svelte-1uha8ag"><header class="app-bar svelte-1uha8ag"><div class="bar-left svelte-1uha8ag"><span class="app-logo svelte-1uha8ag">SQLviz</span> <!> <!></div> <div class="bar-right svelte-1uha8ag"><!> <div class="mode-toggle svelte-1uha8ag" role="group" aria-label="Dashboard mode"><button>Preview</button> <button>Edit</button></div> <button class="theme-btn svelte-1uha8ag"> </button></div></header> <div class="app-body svelte-1uha8ag"><!> <div class="app-main svelte-1uha8ag"><!> <!> <div><!></div></div> <!></div></div> <!> <!>',1);function Hn(f,t){Ye(t,!0);const u=()=>$t(zt,"$editorRef",b),h=()=>$t(Yt,"$filterValues",b),_=()=>$t(yt,"$editMode",b),[b,s]=ea();let d=G(""),p=G(null),C=G(!1),T=G(null),R=G(null),I=G("dark");function H(){v(I,e(I)==="dark"?"light":"dark",!0),e(I)==="light"?document.documentElement.dataset.theme="light":delete document.documentElement.dataset.theme,localStorage.setItem("sqlviz-theme",e(I))}let D=G(null),m=G(it([])),E=G(it([])),y=G(it([])),L=G(!1),A=G(it([])),S=G(!1),$=G(""),Q=G(null),be=0;const ye=W(()=>e(p)!==null&&e(p).rows.length>0),Le=W(()=>e(A).length>=2),Ne=W(()=>e(A).find(n=>n.id===e(D))??null),Ue=W(()=>{var n;return((n=e(p))==null?void 0:n.utility_score)!=null?Math.round(e(p).utility_score*100):null}),Oe=W(()=>{const n=new Set,a=[];for(const o of e(y))for(const l of o.inference_result.filter_controls)n.has(l.variable)||(n.add(l.variable),a.push(l));return a}),Fe=W(()=>e(Oe).length>0);let de=0;async function F(n,a){const o=await fetch(n,{method:"POST",headers:a!==void 0?{"Content-Type":"application/json"}:{},body:a!==void 0?JSON.stringify(a):void 0});if(!o.ok){const l=await o.json().catch(()=>null);throw new Error((l==null?void 0:l.detail)??`${o.status} ${o.statusText}`)}return o.json()}async function ve(n,a){const o=await fetch(n,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify(a)});if(!o.ok){const l=await o.json().catch(()=>null);throw new Error((l==null?void 0:l.detail)??`${o.status} ${o.statusText}`)}return o.json()}async function Z(n){const a=n.map(w=>({panel_id:w.panel_id,inference_result:w.inference_result})),o=await F("/api/v1/compose",a),l=new Map(n.map(w=>[w.panel_id,w.data]));return{...o,rows:o.rows.map(w=>({panels:w.panels.map(M=>({...M,data:l.get(M.panel_id)??[]}))}))}}Jt(async()=>{localStorage.getItem("sqlviz-theme")==="light"&&(v(I,"light"),document.documentElement.dataset.theme="light");const a=await fetch("/api/v1/auth/me");if(a.status===401){await Na("/login");return}const o=await a.json();o.demo&&yt.set(!0);try{const l=await fetch("/api/v1/dashboards").then(M=>M.json());if(v(A,l,!0),l.length===0){if(o.demo){const{sql:M}=await fetch("/api/v1/demo/sql").then(q=>q.json());v(d,M,!0),j()}return}v(D,l[0].id,!0);const w=await fetch(`/api/v1/panels?dashboard_id=${e(D)}`).then(M=>M.json());if(w.length===0)return;w.sort((M,q)=>M.sort_order-q.sort_order),v(m,w.map(M=>M.id),!0),v(E,w.map(M=>M.sql_content),!0),v(d,e(E).join(`;

`),!0)}catch{}});async function j(){if(e(C))return;const n=e(d).split(";").map(a=>a.trim()).filter(a=>a.length>0);if(n.length===0){v(R,'No SQL statements found. Write at least one query separated by ";".');return}v(C,!0),v(R,null);try{if(!e(D)){const l=await F("/api/v1/dashboards",{name:"My Dashboard",sort_order:0});v(D,l.id,!0)}const a=[],o=[];for(let l=0;l<n.length;l++){const w=n[l];v(T,`Statement ${l+1} / ${n.length}…`);let M;e(m)[l]?(await ve(`/api/v1/panels/${e(m)[l]}`,{sql_content:w,sort_order:l}),M=e(m)[l]):M=(await F("/api/v1/panels",{dashboard_id:e(D),name:`Panel ${l+1}`,sql_content:w,sort_order:l})).id,o.push(M);const q=await F(`/api/v1/panels/${M}/execute`);a.push({panel_id:M,...q})}v(m,o,!0),v(E,n,!0),v(y,a,!0),v(T,"Composing layout…"),v(p,await Z(a),!0),v(T,null);try{v(A,await fetch("/api/v1/dashboards").then(l=>l.json()),!0)}catch{}}catch(a){v(R,a instanceof Error?a.message:String(a),!0),v(T,null)}finally{v(C,!1)}}async function fe(n){const a=e(m).indexOf(n);if(a<0)return;try{await fetch(`/api/v1/panels/${n}`,{method:"DELETE"})}catch{le("Delete failed — check the API server.");return}const o=e(y).filter((M,q)=>q!==a),l=e(m).filter((M,q)=>q!==a),w=e(E).filter((M,q)=>q!==a);if(v(y,o,!0),v(m,l,!0),v(E,w,!0),v(d,w.join(`;

`),!0),o.length===0){v(p,null);return}try{v(p,await Z(o),!0)}catch(M){le(M instanceof Error?M.message:"Compose failed after delete.")}}function ge(n){var o,l;const a=e(m).indexOf(n);a<0||(l=(o=u()).focusStatement)==null||l.call(o,a)}function Te(n){const a=e(y).find(o=>o.panel_id===n);if(!a){le("Run the dashboard first to see explainability data.");return}qt.set(a)}async function we(){const n=e($).trim()||"New Dashboard";v(S,!1),v($,"");try{const a=await F("/api/v1/dashboards",{name:n,sort_order:e(A).length});v(A,await fetch("/api/v1/dashboards").then(o=>o.json()),!0),v(D,a.id,!0),v(m,[],!0),v(E,[],!0),v(d,""),v(y,[],!0),v(p,null)}catch(a){le(a instanceof Error?a.message:"Could not create dashboard.")}}function ue(){v(S,!1),v($,"")}async function ie(n){if(!(n===e(D)||e(C)))try{const a=await fetch(`/api/v1/panels?dashboard_id=${n}`).then(o=>o.json());a.sort((o,l)=>o.sort_order-l.sort_order),v(D,n,!0),v(m,a.map(o=>o.id),!0),v(E,a.map(o=>o.sql_content),!0),v(d,e(E).join(`;

`),!0),v(y,[],!0),v(p,null),a.length>0&&j()}catch(a){le(a instanceof Error?a.message:"Could not load dashboard.")}}async function Ee(n,a){try{await ve(`/api/v1/panels/${n}/override`,{field_name:"chart_type",user_value:a});const o=await F(`/api/v1/panels/${n}/execute`);v(y,e(y).map(l=>l.panel_id===n?{panel_id:n,inference_result:o.inference_result,data:o.data}:l),!0),v(p,await Z(e(y)),!0)}catch(o){le(o instanceof Error?o.message:"Chart override failed.")}}function $e(n,a){e(p)&&v(p,{...e(p),rows:e(p).rows.map(o=>({panels:o.panels.map(l=>l.panel_id!==n?l:{...l,final_col_span:a??l.inference_result.col_span})}))},!0)}function Re(n,a){e(p)&&v(p,{...e(p),rows:e(p).rows.map(o=>({panels:o.panels.map(l=>l.panel_id!==n?l:{...l,inference_result:{...l.inference_result,panel_height_px:a??l.inference_result.panel_height_px}})}))},!0)}async function he(n,a){const o=[...e(y)];let l=!1;for(let w=0;w<e(y).length;w++){const q=e(y)[w].inference_result.filter_controls.flatMap(pe=>pe.variable.split(",").map(He=>He.trim()));if(!q.includes(n)||!q.every(pe=>{const He=a[pe];return He!==void 0&&He!==""&&He!==null}))continue;const Tt=Object.fromEntries(q.map(pe=>[pe,a[pe]])),mt=e(m)[w];try{const pe=await F(`/api/v1/panels/${mt}/execute`,{variables:Tt});o[w]={panel_id:mt,...pe},l=!0}catch{}}if(l){v(y,o,!0);try{v(p,await Z(o),!0)}catch{}}}function Pe(n,a){Yt.update(o=>({...o,[n]:a})),clearTimeout(de),de=window.setTimeout(()=>{const o={...h(),[n]:a};he(n,o)},350)}function le(n,a=3500){v(Q,n,!0),clearTimeout(be),be=window.setTimeout(()=>{v(Q,null)},a)}var Ie=Tn(),ne=O(Ie),se=i(ne),ke=i(se),vt=c(i(ke),2);{var Ct=n=>{var a=mn(),o=i(a,!0);r(a),B(()=>{lt(a,"title",e(Ne).name),N(o,e(Ne).name)}),g(n,a)};z(vt,n=>{e(Ne)&&n(Ct)})}var Xe=c(vt,2);{var Ze=n=>{var a=bn(),o=i(a);Ma(o),ka(o,!0);var l=c(o,4);r(a),Zt("submit",a,w=>{w.preventDefault(),we()}),te("keydown",o,w=>{w.key==="Escape"&&ue()}),Sa(o,()=>e($),w=>v($,w)),te("click",l,ue),g(n,a)},et=n=>{var a=yn();te("click",a,()=>{v(S,!0)}),g(n,a)};z(Xe,n=>{e(S)?n(Ze):n(et,-1)})}r(ke);var ut=c(ke,2),ht=i(ut);{var Mt=n=>{var a=wn();let o;var l=i(a);r(a),B(()=>{o=Y(a,1,"score-btn svelte-1uha8ag",null,o,{active:e(L)}),N(l,`Score${e(Ue)!=null?`: ${e(Ue)}`:""}
                    ${e(L)?"▼":"▲"}`)}),te("click",a,()=>v(L,!e(L))),g(n,a)};z(ht,n=>{_()&&n(Mt)})}var tt=c(ht,2),at=i(tt);let Ve;var We=c(at,2);let Ge;r(tt);var Be=c(tt,2),nt=i(Be,!0);r(Be),r(ut),r(se);var _t=c(se,2),ft=i(_t);{var St=n=>{tn(n,{get items(){return e(A)},get activeId(){return e(D)},onSelect:ie})};z(ft,n=>{e(Le)&&n(St)})}var Qe=c(ft,2),Ke=i(Qe);{var gt=n=>{Ta(n,{get controls(){return e(Oe)},get filterVals(){return h()},onChange:Pe})};z(Ke,n=>{e(Fe)&&n(gt)})}var pt=c(Ke,2);{var st=n=>{var a=xn(),o=i(a),l=i(o),w=i(l);let M;var q=c(w);r(l);var De=c(l,4);{var Tt=qe=>{var ze=$n(),bt=c(i(ze),2),sa=i(bt,!0);r(bt),r(ze),B(()=>{lt(ze,"title",e(R)),N(sa,e(R))}),g(qe,ze)},mt=qe=>{var ze=kn(),bt=i(ze,!0);r(ze),B(()=>N(bt,e(T))),g(qe,ze)};z(De,qe=>{e(R)?qe(Tt):e(C)&&e(T)&&e(ye)&&qe(mt,1)})}r(o);var pe=c(o,2),He=i(pe);pn(He,{onRun:j,get disabled(){return e(C)},get theme(){return e(I)},get value(){return e(d)},set value(qe){v(d,qe,!0)}}),r(pe),r(a),B(()=>{l.disabled=e(C),M=Y(w,1,"run-icon svelte-1uha8ag",null,M,{spinning:e(C)}),N(q,` ${(e(C)?e(T)??"Running…":"Run")??""}`)}),te("click",l,j),g(n,a)};z(pt,n=>{_()&&n(st)})}var rt=c(pt,2);let ot;var Nt=i(rt);{var k=n=>{var a=Cn(),o=c(i(a),2),l=i(o,!0);r(o),r(a),B(()=>N(l,e(T)??"Executing…")),g(n,a)},P=n=>{var a=Sn(),o=c(i(a),2),l=i(o,!0);r(o);var w=c(o,2);{var M=q=>{var De=Mn();g(q,De)};z(w,q=>{_()&&q(M)})}r(a),B(()=>N(l,_()?"Press Ctrl+Enter to run and see results here":"Switch to Edit mode to write SQL and create panels")),g(n,a)},U=n=>{Ea(n,{get layout(){return e(p)},onEditSQL:ge,onExplain:Te,onDelete:fe,onChartOverride:Ee,onWidthOverride:$e,onHeightOverride:Re})};z(Nt,n=>{e(C)&&!e(ye)?n(k):e(ye)?e(p)&&n(U,2):n(P,1)})}r(rt),r(Qe);var _e=c(Qe,2);{var K=n=>{Fa(n,{get layout(){return e(p)},onClose:()=>v(L,!1)})};z(_e,n=>{_()&&e(L)&&e(p)&&n(K)})}r(_t),r(ne);var V=c(ne,2);{var ee=n=>{var a=Nn(),o=i(a,!0);r(a),B(()=>N(o,e(Q))),g(n,a)};z(V,n=>{e(Q)&&n(ee)})}var ce=c(V,2);_n(ce,{}),B(()=>{Ve=Y(at,1,"mode-btn svelte-1uha8ag",null,Ve,{active:!_()}),Ge=Y(We,1,"mode-btn svelte-1uha8ag",null,Ge,{active:_()}),lt(Be,"aria-label",e(I)==="dark"?"Switch to light mode":"Switch to dark mode"),lt(Be,"title",e(I)==="dark"?"Light mode":"Dark mode"),N(nt,e(I)==="dark"?"☀":"☾"),ot=Y(rt,1,"dashboard-area svelte-1uha8ag",null,ot,{empty:!e(ye)&&!e(C)})}),te("click",at,()=>yt.set(!1)),te("click",We,()=>yt.set(!0)),te("click",Be,H),g(f,Ie),Je(),s()}xt(["keydown","click"]);export{Hn as component};
