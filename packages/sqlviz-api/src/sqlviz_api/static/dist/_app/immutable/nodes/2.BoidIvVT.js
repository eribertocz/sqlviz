const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["../chunks/ekk7sIKj.js","../chunks/CXyBGMYu.js","../chunks/C0jHkEur.js","../chunks/Cea5cxJJ.js","../assets/editor.B8tIeeJt.css"])))=>i.map(i=>d[i]);
import{b as ra,a as g,f as C,c as J,d as oa}from"../chunks/EVBMHDXH.js";import{w as At,o as Xt,a as ia}from"../chunks/DxICD3qh.js";import{h as xe,i as It,e as Et,b5 as la,b as ca,E as da,ab as va,f as ua,c as ha,s as Ht,d as Pt,S as _a,L as ga,b6 as fa,P as pa,al as ma,aj as lt,b7 as jt,R as Rt,b8 as ba,w as e,b9 as Oe,a3 as ya,t as Ye,F as G,G as it,z as i,y as c,B as n,x as Je,K as W,I as z,v as O,ba as Ot,D as v,bb as wa,bc as $a,a4 as ke,u as ka}from"../chunks/C0jHkEur.js";import{f as xa,a as wt,d as ee,s as S,e as Zt}from"../chunks/CY52XHtr.js";import{l as Y,p as Me,s as re,a as ea,c as bt,b as Ca}from"../chunks/ds6XAry9.js";import{i as I}from"../chunks/DfobnKYw.js";import{s as Q,a as yt,c as Ft,d as Qe,r as Ma,b as Sa}from"../chunks/DL6DCHt6.js";import{g as Na}from"../chunks/DDeCD3qU.js";import{a as Pe,i as Ke,e as pt,F as Ta,D as Ea}from"../chunks/DE_gk0xX.js";import{c as Pa,_ as Da}from"../chunks/CXyBGMYu.js";import{B as La}from"../chunks/Cea5cxJJ.js";function te(f,s,u,h,_){var d;xe&&It();var w=(d=s.$$slots)==null?void 0:d[u],r=!1;w===!0&&(w=s.children,r=!0),w===void 0||w(f,r?()=>h:h)}function Ia(f,s,u,h,_,w){let r=xe;xe&&It();var d=null;xe&&Et.nodeType===la&&(d=Et,It());var b=xe?Et:f,M=new La(b,!1);ca(()=>{const E=s()||null;var R=fa;if(E===null){M.ensure(null,null);return}return M.ensure(E,q=>{if(E){if(d=xe?d:va(E,R),ra(d,d),h){var H=null;xe&&xa(E)&&d.append(H=document.createComment(""));var D=xe?ua(d):d.appendChild(ha());xe&&(D===null?Ht(!1):Pt(D)),h(d,D),H==null||H.remove()}_a.nodes.end=d,q.before(d)}xe&&Pt(q)}),()=>{}},da),ga(()=>{}),r&&(Ht(!0),Pt(b))}function ta(f=!1){const s=pa,u=s.l.u;if(!u)return;let h=()=>Oe(s.s);if(f){let _=0,w={};const r=ya(()=>{let d=!1;const b=s.s;for(const M in b)b[M]!==w[M]&&(w[M]=b[M],d=!0);return d&&_++,_});h=()=>e(r)}u.b.length&&ma(()=>{Ut(s,h),jt(u.b)}),lt(()=>{const _=Rt(()=>u.m.map(ba));return()=>{for(const w of _)typeof w=="function"&&w()}}),u.a.length&&lt(()=>{Ut(s,h),jt(u.a)})}function Ut(f,s){if(f.l.s)for(const u of f.l.s)e(u);s()}var Ra=C('<div class="no-data svelte-7vbfso"><p class="svelte-7vbfso">Score available after dashboard execution.</p> <p class="hint svelte-7vbfso">V0.2 backend required for utility scoring.</p></div>'),qa=C('<span class="low-good-hint svelte-7vbfso">(low=good)</span>'),za=C('<div class="breakdown-row svelte-7vbfso"><span class="dim-name svelte-7vbfso"> </span> <div class="mini-track svelte-7vbfso"><div class="mini-fill svelte-7vbfso"></div></div> <span> <!></span></div>'),Aa=C('<div class="breakdown-block svelte-7vbfso"></div>'),Oa=C('<button class="action-btn apply svelte-7vbfso">Apply</button>'),Ba=C('<div class="suggestion svelte-7vbfso"><div class="suggestion-text svelte-7vbfso"><span class="warn-icon svelte-7vbfso">⚠</span> <div><strong> </strong> <span class="suggestion-body svelte-7vbfso"> </span> <span class="impact svelte-7vbfso"> </span></div></div> <div class="suggestion-actions svelte-7vbfso"><!> <button class="action-btn dismiss svelte-7vbfso">Dismiss</button></div></div>'),Ha=C('<div class="suggestions-block svelte-7vbfso"><span class="suggestions-label svelte-7vbfso">Sugerencias</span> <!></div>'),ja=C('<div class="utility-block svelte-7vbfso"><div class="score-row svelte-7vbfso"><span class="score-heading svelte-7vbfso">Utility Score</span> <span> </span></div> <div class="score-track svelte-7vbfso"><div class="score-fill svelte-7vbfso"></div></div></div> <!> <!>',1),Fa=C('<aside class="score-panel svelte-7vbfso" aria-label="Dashboard Score"><div class="panel-header svelte-7vbfso"><span class="panel-title svelte-7vbfso">Dashboard Score</span> <button class="close-btn svelte-7vbfso" aria-label="Close score panel">×</button></div> <!></aside>');function Ua(f,s){Ye(s,!0);function u($){return $>=85?{text:"Excellent",cls:"excellent"}:$>=70?{text:"Good",cls:"good"}:$>=55?{text:"Fair",cls:"fair"}:{text:"Needs work",cls:"needs-work"}}const h=W(()=>Math.round((s.layout.utility_score??0)*100)),_=W(()=>u(e(h))),w=W(()=>(s.layout.suggestions??[]).slice().sort(($,L)=>L.score_impact-$.score_impact)),r=W(()=>s.layout.utility_breakdown??{}),d=W(()=>s.layout.utility_score!=null);let b=G(it(new Set));const M=W(()=>e(w).filter($=>!e(b).has($.panel_id+$.suggestion)));function E($){v(b,new Set([...e(b),$.panel_id+$.suggestion]),!0)}var R=Fa(),q=i(R),H=c(i(q),2);n(q);var D=c(q,2);{var y=$=>{var L=Ra();g($,L)},P=$=>{var L=ja(),B=z(L),T=i(B),k=c(i(T),2),K=i(k);n(k),n(T);var me=c(T,2),be=i(me);n(me),n(B);var De=c(B,2);{var Se=de=>{var V=Aa();Pe(V,21,()=>Object.entries(e(r)),([ve,X])=>ve,(ve,X)=>{var j=W(()=>Ot(e(X),2));let ge=()=>e(j)[0],fe=()=>e(j)[1];const Ne=W(()=>Math.round(Number(fe())*100)),ye=W(()=>ge()==="cognitive_load"||ge()==="space_waste");var ue=za(),ie=i(ue),Te=i(ie,!0);n(ie);var we=c(ie,2),Le=i(we);n(we);var he=c(we,2);let Ee;var le=i(he),Ie=c(le);{var ae=se=>{var $e=qa();g(se,$e)};I(Ie,se=>{e(ye)&&se(ae)})}n(he),n(ue),O(se=>{S(Te,ge()),yt(Le,`width: ${e(Ne)??""}%`),Ee=Q(he,1,"dim-value svelte-7vbfso",null,Ee,{"low-good":e(ye)}),S(le,`${se??""} `)},[()=>Number(fe()).toFixed(2)]),g(ve,ue)}),n(V),g(de,V)},Be=W(()=>Object.keys(e(r)).length>0);I(De,de=>{e(Be)&&de(Se)})}var qe=c(De,2);{var He=de=>{var V=Ha(),ve=c(i(V),2);Pe(ve,17,()=>e(M),X=>X.panel_id+X.suggestion,(X,j)=>{var ge=Ba(),fe=i(ge),Ne=c(i(fe),2),ye=i(Ne),ue=i(ye,!0);n(ye);var ie=c(ye,2),Te=i(ie);n(ie);var we=c(ie,2),Le=i(we);n(we),n(Ne),n(fe);var he=c(fe,2),Ee=i(he);{var le=ae=>{var se=Oa();ee("click",se,()=>{var $e;return($e=s.onApplySuggestion)==null?void 0:$e.call(s,e(j).panel_id,e(j).action)}),g(ae,se)};I(Ee,ae=>{e(j).action&&s.onApplySuggestion&&ae(le)})}var Ie=c(Ee,2);n(he),n(ge),O(ae=>{S(ue,e(j).panel_label??e(j).panel_id),S(Te,`— ${e(j).suggestion??""}`),S(Le,`(+${ae??""}% utility)`)},[()=>Math.round(e(j).score_impact*100)]),ee("click",Ie,()=>E(e(j))),g(X,ge)}),n(V),g(de,V)};I(qe,de=>{e(M).length>0&&de(He)})}O(()=>{Q(k,1,`score-value ${e(_).cls??""}`,"svelte-7vbfso"),S(K,`${e(h)??""} / 100 · ${e(_).text??""}`),yt(be,`width: ${e(h)??""}%`)}),g($,L)};I(D,$=>{e(d)?$(P,-1):$(y)})}n(R),ee("click",H,function(...$){var L;(L=s.onClose)==null||L.apply(this,$)}),g(f,R),Je()}wt(["click"]);wa();/**
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
 */const Va=f=>{for(const s in f)if(s.startsWith("aria-")||s==="role"||s==="title")return!0;return!1};/**
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
 */const Wt=(...f)=>f.filter((s,u,h)=>!!s&&s.trim()!==""&&h.indexOf(s)===u).join(" ").trim();var Ga=oa("<svg><!><!></svg>");function oe(f,s){const u=Y(s,["children","$$slots","$$events","$$legacy"]),h=Y(u,["name","color","size","strokeWidth","absoluteStrokeWidth","iconNode"]);Ye(s,!1);let _=Me(s,"name",8,void 0),w=Me(s,"color",8,"currentColor"),r=Me(s,"size",8,24),d=Me(s,"strokeWidth",8,2),b=Me(s,"absoluteStrokeWidth",8,!1),M=Me(s,"iconNode",24,()=>[]);ta();var E=Ga();Ft(E,(H,D,y)=>({...Wa,...H,...h,width:r(),height:r(),stroke:w(),"stroke-width":D,class:y}),[()=>Va(h)?void 0:{"aria-hidden":"true"},()=>(Oe(b()),Oe(d()),Oe(r()),Rt(()=>b()?Number(d())*24/Number(r()):d())),()=>(Oe(Wt),Oe(_()),Oe(u),Rt(()=>Wt("lucide-icon","lucide",_()?`lucide-${_()}`:"",u.class)))]);var R=i(E);Pe(R,1,M,Ke,(H,D)=>{var y=W(()=>Ot(e(D),2));let P=()=>e(y)[0],$=()=>e(y)[1];var L=J(),B=z(L);Ia(B,P,!0,(T,k)=>{Ft(T,()=>({...$()}))}),g(H,L)});var q=c(R);te(q,s,"default",{}),n(E),g(f,E),Je()}function aa(f,s){const u=Y(s,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["path",{d:"M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"}]];oe(f,re({name:"activity"},()=>u,{get iconNode(){return h},children:(_,w)=>{var r=J(),d=z(r);te(d,s,"default",{}),g(_,r)},$$slots:{default:!0}}))}function Qa(f,s){const u=Y(s,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"M7 11h8"}],["path",{d:"M7 16h3"}],["path",{d:"M7 6h12"}]];oe(f,re({name:"chart-bar-decreasing"},()=>u,{get iconNode(){return h},children:(_,w)=>{var r=J(),d=z(r);te(d,s,"default",{}),g(_,r)},$$slots:{default:!0}}))}function mt(f,s){const u=Y(s,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"M7 16h8"}],["path",{d:"M7 11h12"}],["path",{d:"M7 6h3"}]];oe(f,re({name:"chart-bar"},()=>u,{get iconNode(){return h},children:(_,w)=>{var r=J(),d=z(r);te(d,s,"default",{}),g(_,r)},$$slots:{default:!0}}))}function sa(f,s){const u=Y(s,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}],["path",{d:"m19 9-5 5-4-4-3 3"}]];oe(f,re({name:"chart-line"},()=>u,{get iconNode(){return h},children:(_,w)=>{var r=J(),d=z(r);te(d,s,"default",{}),g(_,r)},$$slots:{default:!0}}))}function Ka(f,s){const u=Y(s,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["path",{d:"M21 12c.552 0 1.005-.449.95-.998a10 10 0 0 0-8.953-8.951c-.55-.055-.998.398-.998.95v8a1 1 0 0 0 1 1z"}],["path",{d:"M21.21 15.89A10 10 0 1 1 8 2.83"}]];oe(f,re({name:"chart-pie"},()=>u,{get iconNode(){return h},children:(_,w)=>{var r=J(),d=z(r);te(d,s,"default",{}),g(_,r)},$$slots:{default:!0}}))}function Ya(f,s){const u=Y(s,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["circle",{cx:"7.5",cy:"7.5",r:".5",fill:"currentColor"}],["circle",{cx:"18.5",cy:"5.5",r:".5",fill:"currentColor"}],["circle",{cx:"11.5",cy:"11.5",r:".5",fill:"currentColor"}],["circle",{cx:"7.5",cy:"16.5",r:".5",fill:"currentColor"}],["circle",{cx:"17.5",cy:"14.5",r:".5",fill:"currentColor"}],["path",{d:"M3 3v16a2 2 0 0 0 2 2h16"}]];oe(f,re({name:"chart-scatter"},()=>u,{get iconNode(){return h},children:(_,w)=>{var r=J(),d=z(r);te(d,s,"default",{}),g(_,r)},$$slots:{default:!0}}))}function Dt(f,s){const u=Y(s,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["line",{x1:"4",x2:"20",y1:"9",y2:"9"}],["line",{x1:"4",x2:"20",y1:"15",y2:"15"}],["line",{x1:"10",x2:"8",y1:"3",y2:"21"}],["line",{x1:"16",x2:"14",y1:"3",y2:"21"}]];oe(f,re({name:"hash"},()=>u,{get iconNode(){return h},children:(_,w)=>{var r=J(),d=z(r);te(d,s,"default",{}),g(_,r)},$$slots:{default:!0}}))}function Bt(f,s){const u=Y(s,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["rect",{width:"7",height:"9",x:"3",y:"3",rx:"1"}],["rect",{width:"7",height:"5",x:"14",y:"3",rx:"1"}],["rect",{width:"7",height:"9",x:"14",y:"12",rx:"1"}],["rect",{width:"7",height:"5",x:"3",y:"16",rx:"1"}]];oe(f,re({name:"layout-dashboard"},()=>u,{get iconNode(){return h},children:(_,w)=>{var r=J(),d=z(r);te(d,s,"default",{}),g(_,r)},$$slots:{default:!0}}))}function Vt(f,s){const u=Y(s,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["path",{d:"M2 5h20"}],["path",{d:"M6 12h12"}],["path",{d:"M9 19h6"}]];oe(f,re({name:"list-filter"},()=>u,{get iconNode(){return h},children:(_,w)=>{var r=J(),d=z(r);te(d,s,"default",{}),g(_,r)},$$slots:{default:!0}}))}function Ja(f,s){const u=Y(s,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["path",{d:"M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"}]];oe(f,re({name:"table-2"},()=>u,{get iconNode(){return h},children:(_,w)=>{var r=J(),d=z(r);te(d,s,"default",{}),g(_,r)},$$slots:{default:!0}}))}function pe(f,s){const u=Y(s,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["path",{d:"M16 7h6v6"}],["path",{d:"m22 7-8.5 8.5-5-5L2 17"}]];oe(f,re({name:"trending-up"},()=>u,{get iconNode(){return h},children:(_,w)=>{var r=J(),d=z(r);te(d,s,"default",{}),g(_,r)},$$slots:{default:!0}}))}function Lt(f,s){const u=Y(s,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["path",{d:"m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"}],["path",{d:"M12 9v4"}],["path",{d:"M12 17h.01"}]];oe(f,re({name:"triangle-alert"},()=>u,{get iconNode(){return h},children:(_,w)=>{var r=J(),d=z(r);te(d,s,"default",{}),g(_,r)},$$slots:{default:!0}}))}function Gt(f,s){const u=Y(s,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["path",{d:"M10 14.66v1.626a2 2 0 0 1-.976 1.696A5 5 0 0 0 7 21.978"}],["path",{d:"M14 14.66v1.626a2 2 0 0 0 .976 1.696A5 5 0 0 1 17 21.978"}],["path",{d:"M18 9h1.5a1 1 0 0 0 0-5H18"}],["path",{d:"M4 22h16"}],["path",{d:"M6 9a6 6 0 0 0 12 0V3a1 1 0 0 0-1-1H7a1 1 0 0 0-1 1z"}],["path",{d:"M6 9H4.5a1 1 0 0 1 0-5H6"}]];oe(f,re({name:"trophy"},()=>u,{get iconNode(){return h},children:(_,w)=>{var r=J(),d=z(r);te(d,s,"default",{}),g(_,r)},$$slots:{default:!0}}))}function Ce(f,s){const u=Y(s,["children","$$slots","$$events","$$legacy"]);/**
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
 */const h=[["path",{d:"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"}],["path",{d:"M16 3.128a4 4 0 0 1 0 7.744"}],["path",{d:"M22 21v-2a4 4 0 0 0-3-3.87"}],["circle",{cx:"9",cy:"7",r:"4"}]];oe(f,re({name:"users"},()=>u,{get iconNode(){return h},children:(_,w)=>{var r=J(),d=z(r);te(d,s,"default",{}),g(_,r)},$$slots:{default:!0}}))}const Qt={kpi_overview:Dt,kpi_performance:pe,financial_kpi:Dt,sales_kpi:Dt,hr_overview:Ce,trend_analysis:pe,financial_trend:pe,product_growth:pe,sales_performance:pe,marketing_performance:pe,hr_trend:pe,ops_monitoring:aa,user_lifecycle:Ce,user_retention:Ce,retention_analysis:Ce,cohort_analysis:Ce,product_retention:Ce,funnel_analysis:Vt,product_funnel:Vt,financial_dashboard:pe,financial_comparison:mt,sales_dashboard:pe,sales_ranking:Gt,marketing_analytics:sa,marketing_comparison:mt,product_analytics:Ce,hr_analytics:Ce,comparison_analysis:mt,competitive_analysis:mt,ranking_analysis:Gt,distribution_analysis:Qa,correlation_analysis:Ya,composition_analysis:Ka,anomaly_detection:Lt,anomaly_monitoring:Lt,incident_monitoring:Lt,data_detail:Ja,analytics_overview:Bt},Kt={finance:pe,product:Ce,marketing:sa,hr:Ce,ops:aa,sales:pe,analytics:Bt};function Xa(f,s,u){return f&&Qt[f]?Qt[f]:s&&Kt[s]?Kt[s]:Bt}var Za=C('<li><button><span class="panel-icon svelte-609rsk"><!></span> <span class="panel-title svelte-609rsk"> </span></button></li>'),es=C('<nav class="dashboard-sidebar svelte-609rsk" aria-label="Dashboard navigation"><div class="sidebar-label svelte-609rsk">Dashboards</div> <ul class="panel-list svelte-609rsk"></ul></nav>');function ts(f,s){Ye(s,!0);let u=Me(s,"activeId",3,null);var h=es(),_=c(i(h),2);Pe(_,21,()=>s.items,w=>w.id,(w,r)=>{const d=W(()=>Xa(e(r).dashboard_hint,e(r).dashboard_domain));var b=Za(),M=i(b);let E;var R=i(M),q=i(R);Pa(q,()=>e(d),(y,P)=>{P(y,{size:14})}),n(R);var H=c(R,2),D=i(H,!0);n(H),n(M),n(b),O(()=>{E=Q(M,1,"panel-item svelte-609rsk",null,E,{active:e(r).id===u()}),Qe(M,"title",e(r).name),S(D,e(r).name)}),ee("click",M,()=>{var y;return(y=s.onSelect)==null?void 0:y.call(s,e(r).id)}),g(w,b)}),n(_),n(h),g(f,h),Je()}wt(["click"]);const qt=At(null);var as=C('<div class="banner fallback svelte-10vh4gh"><span class="banner-icon svelte-10vh4gh">⚠</span> <div><strong class="svelte-10vh4gh">Inference without data</strong> <p class="svelte-10vh4gh"> </p></div></div>'),ss=C('<div class="intent-desc svelte-10vh4gh"> </div>'),ns=C('<li class="signal-item svelte-10vh4gh"><span class="signal-dot svelte-10vh4gh">✓</span> <span class="signal-name svelte-10vh4gh"> </span> <span class="signal-score svelte-10vh4gh"> </span></li>'),rs=C('<div class="subsection-title svelte-10vh4gh">Key signals</div> <ul class="signal-list svelte-10vh4gh"></ul>',1),os=C('<p class="muted-note svelte-10vh4gh">Signal data unavailable — run the panel to see details.</p>'),Yt=C('<div class="score-row svelte-10vh4gh"><span> </span> <div class="bar-track svelte-10vh4gh"><div></div></div> <span> </span></div>'),is=C('<div class="subsection-title svelte-10vh4gh">Intent scores</div> <div class="score-bars svelte-10vh4gh"></div>',1),ls=C('<p class="chart-desc svelte-10vh4gh"> </p>'),cs=C('<div class="subsection-title svelte-10vh4gh">Chart scores</div> <div class="score-bars svelte-10vh4gh"></div>',1),ds=C('<li class="error-item svelte-10vh4gh"> </li>'),vs=C('<div class="subsection-title svelte-10vh4gh">Errors</div> <ul class="error-list svelte-10vh4gh"></ul>',1),us=C('<span class="timing-module svelte-10vh4gh"> </span> <span class="timing-ms svelte-10vh4gh"> </span>',1),hs=C('<div class="subsection-title svelte-10vh4gh">Module timings</div> <div class="timings-grid svelte-10vh4gh"></div>',1),_s=C('<div class="backdrop svelte-10vh4gh" role="presentation"></div> <aside class="explain-drawer svelte-10vh4gh" aria-label="Explainability panel"><div class="drawer-header svelte-10vh4gh"><h2 class="drawer-title svelte-10vh4gh">Why this chart?</h2> <button class="close-btn svelte-10vh4gh" aria-label="Close">✕</button></div> <div class="drawer-body svelte-10vh4gh"><!> <section class="section svelte-10vh4gh"><h3 class="section-title svelte-10vh4gh">Detected intent</h3> <div class="intent-badge svelte-10vh4gh"><span class="intent-icon svelte-10vh4gh"> </span> <div><div class="intent-name svelte-10vh4gh"> </div> <!></div></div> <!> <!></section> <section class="section svelte-10vh4gh"><h3 class="section-title svelte-10vh4gh">Selected chart</h3> <div class="chart-badge svelte-10vh4gh"><strong class="svelte-10vh4gh"> </strong> <!></div> <!></section> <section class="section svelte-10vh4gh"><h3 class="section-title svelte-10vh4gh">Inference confidence</h3> <div class="quality-row svelte-10vh4gh"><span> </span></div> <p class="quality-detail svelte-10vh4gh"> </p> <!></section> <section class="section section-diag svelte-10vh4gh"><h3 class="section-title svelte-10vh4gh">Diagnostics</h3> <div class="diag-grid svelte-10vh4gh"><span class="diag-label svelte-10vh4gh">State</span> <span class="diag-value svelte-10vh4gh"><span> </span></span> <span class="diag-label svelte-10vh4gh">Trace</span> <code class="diag-value diag-mono svelte-10vh4gh"> </code> <span class="diag-label svelte-10vh4gh">Time</span> <span class="diag-value diag-mono svelte-10vh4gh"> </span> <span class="diag-label svelte-10vh4gh">Fingerprint</span> <code class="diag-value diag-mono svelte-10vh4gh"> </code> <span class="diag-label svelte-10vh4gh">Engine</span> <span class="diag-value diag-mono svelte-10vh4gh"> </span></div> <!></section></div></aside>',1);function gs(f,s){Ye(s,!1);const u=()=>bt(qt,"$explainTarget",h),[h,_]=ea(),w={has_group_by:"Groups results with GROUP BY",has_order_by:"Results are ordered sequentially",has_order_by_desc:"Results ordered descending (ranking)",has_limit:"Uses TOP/LIMIT (top-N records)",has_aggregation:"Uses aggregation (SUM, COUNT, AVG…)",has_sum:"Uses SUM aggregate",has_count:"Uses COUNT aggregate",has_avg:"Uses AVG aggregate",has_window_function:"Window function (RANK, ROW_NUMBER…)",has_cte:"Uses Common Table Expression (WITH…)",has_join:"Joins multiple tables",has_where:"Filters data with WHERE",has_date_column:"Contains a date/time column",has_numeric_column:"Contains numeric columns",has_string_column:"Contains text/string columns",has_single_numeric_column:"Returns a single numeric value",has_two_numeric_columns:"Returns two numeric columns (x/y pair)",has_temporal_dimension:"Temporal grouping (date/time)",has_geographic_dimension:"Geographic grouping (location)",has_revenue_metric:"Revenue or monetary metric detected",has_product_entity:"Product or item entity detected",has_customer_entity:"Customer or user entity detected",has_distinct:"Uses DISTINCT",has_case_when:"Contains CASE WHEN logic",has_outliers:"Data contains statistical outliers",has_outliers_detected:"Outlier values detected in results",has_partition_by:"Uses PARTITION BY",has_subquery:"Contains a subquery",result_row_count_is_1:"Returns exactly 1 row (single metric)",result_column_count_is_1:"Returns exactly 1 column",result_is_wide_table:"Wide table — many columns, general data",numeric_column_ratio:"High proportion of numeric columns",date_column_ratio:"High proportion of date columns",row_count_normalized:"Number of result rows (non-zero)",cardinality_ratio:"Category uniqueness ratio",temporal_cardinality:"Distinct time periods in result",trend_strength:"Statistical trend detected in values",no_group_by:"No GROUP BY clause",no_aggregation:"No aggregate functions",no_temporal_dimension:"No temporal dimension present",no_order_by_desc:"Not ordered descending",no_numeric_column:"No numeric output columns",no_case_when:"No conditional logic",no_customer_entity:"No customer entity found",no_count:"No COUNT aggregate",order_desc_and_limit:"Top-N ranking pattern (DESC + LIMIT)",high_cardinality:"Many unique categories",low_cardinality:"Few distinct categories",multiple_rows:"Returns multiple rows",single_numeric_column:"Single numeric column in result",high_col_count:"Many columns selected",group_by_count_gte_2:"Groups by 2 or more dimensions",part_of_whole_score:"Part-of-whole pattern (share/percentage)",is_monotonic_decreasing:"Values consistently decrease (funnel)",distinct_entity_count_over_time:"Distinct users counted over time (retention)",has_percentile:"Uses percentile/quantile function"},r={trend:{label:"Temporal Trend",icon:"↗",description:"Values change over time. The SQL groups by a date or sequential column with an ORDER BY."},comparison:{label:"Comparison",icon:"⇄",description:"Values compared across distinct categories such as products, regions or segments."},kpi:{label:"Key Metric (KPI)",icon:"#",description:"A single aggregate number — the SQL returns one summary value with no GROUP BY."},distribution:{label:"Distribution",icon:"∿",description:"How values are spread across a range or bucket (histogram-style data)."},geospatial:{label:"Geographic",icon:"⊕",description:"Data has a geographic dimension such as country, region or coordinates."},relationship:{label:"Correlation",icon:"◎",description:"Two numeric dimensions that may be correlated — scatter-plot pattern."},composition:{label:"Composition",icon:"◔",description:"Parts that add up to a whole — market share, budget split, category breakdown."},retention:{label:"Retention / Cohort",icon:"⟲",description:"Tracks how many users or customers return over time (COUNT DISTINCT over temporal)."},funnel:{label:"Funnel",icon:"▽",description:"Sequential steps where values consistently decrease — conversion or drop-off."},ranking:{label:"Ranking / Top-N",icon:"▲",description:"Top values sorted descending with a LIMIT — leaderboard or best performers."},detail:{label:"Tabular Detail",icon:"≡",description:"General table of records with no clear analytical pattern."},anomaly:{label:"Anomaly Detection",icon:"!",description:"Highlights outlier or unusual values in the data."}},d={line:{label:"Line Chart",description:"Shows how a value evolves over time or a sequential dimension."},bar:{label:"Bar Chart",description:"Compares discrete values across categories side by side."},bar_horizontal:{label:"Horizontal Bar",description:"Same as bar but rotated — better when category labels are long."},pie:{label:"Pie Chart",description:"Shows each category as a fraction of the total."},scatter:{label:"Scatter Plot",description:"Reveals correlations between two numeric variables."},histogram:{label:"Histogram",description:"Distribution of a single numeric variable across value buckets."},table:{label:"Table",description:"Presents all records when no single visualization fits better."},kpi:{label:"KPI Card",description:"A single headline number — the most important metric, front and center."}},b={high:{label:"High confidence",cls:"positive",detail:"The SQL pattern clearly matches the detected intent. This visualization is highly reliable."},medium:{label:"Medium confidence",cls:"neutral",detail:"The SQL pattern partially matches. The result is likely correct but some ambiguity exists."},low:{label:"Low confidence",cls:"negative",detail:"The SQL pattern is ambiguous. Consider rephrasing your query for clearer inference."}};function M(T){return T.explanation.filter(k=>k.contribution>0).sort((k,K)=>K.contribution-k.contribution).slice(0,5)}function E(T){return w[T]??T.replace(/_/g," ")}function R(T){return r[T]??{label:T,icon:"?",description:""}}function q(T){return d[T]??{label:T,description:""}}function H(T){return b[T]??b.low}function D(T,k){return k===0?"4%":Math.max(4,Math.round(T/k*100))+"%"}function y(){qt.set(null)}function P(T){T.key==="Escape"&&y()}ta();var $=J();Zt("keydown",$a,P);var L=z($);{var B=T=>{const k=ke(()=>u().inference_result),K=ke(()=>M(e(k))),me=ke(()=>R(e(k).intent_winner)),be=ke(()=>q(e(k).chart_winner)),De=ke(()=>H(e(k).chart_quality)),Se=ke(()=>[{intent:e(k).intent_winner,raw_score:e(k).intent_raw_score},...e(k).intent_alternatives]),Be=ke(()=>Math.max(...e(Se).map(x=>x.raw_score),.01)),qe=ke(()=>e(k).chart_alternatives),He=ke(()=>[{chart:e(k).chart_winner,raw_score:e(k).chart_raw_score},...e(qe)]),de=ke(()=>Math.max(...e(He).map(x=>x.raw_score),.01));var V=_s(),ve=z(V),X=c(ve,2),j=i(X),ge=c(i(j),2);n(j);var fe=c(j,2),Ne=i(fe);{var ye=x=>{var t=as(),a=c(i(t),2),o=c(i(a),2),l=i(o,!0);n(o),n(a),n(t),O(()=>S(l,e(k).fallback_reason||"The query could not be executed, so inference ran on SQL structure only.")),g(x,t)};I(Ne,x=>{e(k).fallback_applied&&x(ye)})}var ue=c(Ne,2),ie=c(i(ue),2),Te=i(ie),we=i(Te,!0);n(Te);var Le=c(Te,2),he=i(Le),Ee=i(he,!0);n(he);var le=c(he,2);{var Ie=x=>{var t=ss(),a=i(t,!0);n(t),O(()=>S(a,e(me).description)),g(x,t)};I(le,x=>{e(me).description&&x(Ie)})}n(Le),n(ie);var ae=c(ie,2);{var se=x=>{var t=rs(),a=c(z(t),2);Pe(a,5,()=>e(K),Ke,(o,l)=>{var m=ns(),p=c(i(m),2),N=i(p,!0);n(p);var F=c(p,2),U=i(F,!0);n(F),n(m),O((Z,A)=>{S(N,Z),S(U,A)},[()=>E(e(l).signal),()=>e(l).contribution.toFixed(2)]),g(o,m)}),n(a),g(x,t)},$e=x=>{var t=os();g(x,t)};I(ae,x=>{e(K).length>0?x(se):x($e,-1)})}var ct=c(ae,2);{var $t=x=>{var t=is(),a=c(z(t),2);Pe(a,5,()=>e(Se),Ke,(o,l,m)=>{var p=Yt(),N=i(p);Q(N,1,"score-label svelte-10vh4gh",null,{},{winner:m===0});var F=i(N,!0);n(N);var U=c(N,2),Z=i(U);Q(Z,1,"bar-fill svelte-10vh4gh",null,{},{"bar-winner":m===0}),n(U);var A=c(U,2);Q(A,1,"score-value svelte-10vh4gh",null,{},{winner:m===0});var ce=i(A,!0);n(A),n(p),O((ne,_e,Re)=>{S(F,ne),yt(Z,`width: ${_e??""}`),S(ce,Re)},[()=>R(e(l).intent).label,()=>D(e(l).raw_score,e(Be)),()=>e(l).raw_score.toFixed(2)]),g(o,p)}),n(a),g(x,t)};I(ct,x=>{e(Se).length>1&&x($t)})}n(ue);var Xe=c(ue,2),Ze=c(i(Xe),2),et=i(Ze),dt=i(et,!0);n(et);var vt=c(et,2);{var kt=x=>{var t=ls(),a=i(t,!0);n(t),O(()=>S(a,e(be).description)),g(x,t)};I(vt,x=>{e(be).description&&x(kt)})}n(Ze);var tt=c(Ze,2);{var at=x=>{var t=cs(),a=c(z(t),2);Pe(a,5,()=>e(He),Ke,(o,l,m)=>{var p=Yt(),N=i(p);Q(N,1,"score-label svelte-10vh4gh",null,{},{winner:m===0});var F=i(N,!0);n(N);var U=c(N,2),Z=i(U);Q(Z,1,"bar-fill svelte-10vh4gh",null,{},{"bar-winner":m===0}),n(U);var A=c(U,2);Q(A,1,"score-value svelte-10vh4gh",null,{},{winner:m===0});var ce=i(A,!0);n(A),n(p),O((ne,_e,Re)=>{S(F,ne),yt(Z,`width: ${_e??""}`),S(ce,Re)},[()=>q(e(l).chart).label,()=>D(e(l).raw_score,e(de)),()=>e(l).raw_score.toFixed(2)]),g(o,p)}),n(a),g(x,t)};I(tt,x=>{e(qe).length>0&&x(at)})}n(Xe);var je=c(Xe,2),Fe=c(i(je),2),Ue=i(Fe),ze=i(Ue,!0);n(Ue),n(Fe);var st=c(Fe,2),ut=i(st,!0);n(st);var ht=c(st,2);{var xt=x=>{var t=vs(),a=c(z(t),2);Pe(a,5,()=>e(k).errors,Ke,(o,l)=>{var m=ds(),p=i(m,!0);n(m),O(()=>S(p,e(l))),g(o,m)}),n(a),g(x,t)};I(ht,x=>{e(k).errors.length>0&&x(xt)})}n(je);var We=c(je,2),Ve=c(i(We),2),nt=c(i(Ve),2),Ge=i(nt),Ct=i(Ge,!0);n(Ge),n(nt);var Ae=c(nt,4),_t=i(Ae,!0);n(Ae);var rt=c(Ae,4),Mt=i(rt);n(rt);var ot=c(rt,4),St=i(ot);n(ot);var gt=c(ot,4),Nt=i(gt,!0);n(gt),n(Ve);var ft=c(Ve,2);{var Tt=x=>{var t=hs(),a=c(z(t),2);Pe(a,5,()=>Object.entries(e(k).module_timings),Ke,(o,l)=>{var m=W(()=>Ot(e(l),2));let p=()=>e(m)[0],N=()=>e(m)[1];var F=us(),U=z(F),Z=i(U,!0);n(U);var A=c(U,2),ce=i(A);n(A),O(ne=>{S(Z,p()),S(ce,`${ne??""} ms`)},[()=>N().toFixed(1)]),g(o,F)}),n(a),g(x,t)};I(ft,x=>{e(k).module_timings&&x(Tt)})}n(We),n(fe),n(X),O((x,t)=>{S(we,e(me).icon),S(Ee,e(me).label),S(dt,e(be).label),Q(Ue,1,`quality-badge ${e(De).cls??""}`,"svelte-10vh4gh"),S(ze,e(De).label),S(ut,e(De).detail),Q(Ge,1,`state-badge state-${e(k).execution_state??"success"??""}`,"svelte-10vh4gh"),S(Ct,e(k).execution_state??"success"),S(_t,e(k).trace_id??"—"),S(Mt,`${x??""} ms`),S(St,`${t??""}…`),S(Nt,e(k).engine_version)},[()=>e(k).elapsed_ms.toFixed(1),()=>e(k).fingerprint.slice(0,12)]),ee("click",ve,y),ee("keydown",ve,()=>{}),ee("click",ge,y),g(T,V)};I(L,T=>{u()&&T(B)})}g(f,$),Je(),_()}wt(["click","keydown"]);const zt=At({});var fs=C('<div class="editor-loading svelte-1dhf0v9">Loading editor…</div>'),ps=C('<div class="editor-host svelte-1dhf0v9"><!> <div></div></div>');function ms(f,s){Ye(s,!0);let u=Me(s,"value",15,""),h=Me(s,"disabled",3,!1),_=Me(s,"theme",3,"dark"),w,r=null,d=null,b=G(!1),M=!1;Xt(async()=>{window.MonacoEnvironment||(window.MonacoEnvironment={getWorker(y,P){return new Worker(URL.createObjectURL(new Blob(["self.onmessage=function(){}"],{type:"text/javascript"})))}});try{const y=await Da(()=>import("../chunks/ekk7sIKj.js").then(P=>P.b),__vite__mapDeps([0,1,2,3,4]),import.meta.url);y.editor.defineTheme("sqlviz-dark",{base:"vs-dark",inherit:!0,rules:[{token:"keyword",foreground:"a78bfa"},{token:"string",foreground:"22c55e"},{token:"comment",foreground:"64748b",fontStyle:"italic"},{token:"number",foreground:"f59e0b"}],colors:{"editor.background":"#0f172a","editor.foreground":"#f1f5f9","editor.lineHighlightBackground":"#1e293b","editor.selectionBackground":"#6366f133","editorLineNumber.foreground":"#475569","editorLineNumber.activeForeground":"#94a3b8","editorCursor.foreground":"#6366f1","scrollbarSlider.background":"#334155","scrollbarSlider.hoverBackground":"#475569","editorBracketMatch.background":"#6366f120","editorBracketMatch.border":"#6366f1"}}),y.editor.defineTheme("sqlviz-light",{base:"vs",inherit:!0,rules:[{token:"keyword",foreground:"4f46e5"},{token:"string",foreground:"16a34a"},{token:"comment",foreground:"64748b",fontStyle:"italic"},{token:"number",foreground:"d97706"}],colors:{"editor.background":"#ffffff","editor.foreground":"#0f172a","editor.lineHighlightBackground":"#f8fafc","editor.selectionBackground":"#6366f133","editorLineNumber.foreground":"#94a3b8","editorLineNumber.activeForeground":"#64748b","editorCursor.foreground":"#6366f1","scrollbarSlider.background":"#e2e8f0","scrollbarSlider.hoverBackground":"#cbd5e1","editorBracketMatch.background":"#6366f120","editorBracketMatch.border":"#6366f1"}}),r=y.editor.create(w,{value:u(),language:"sql",theme:_()==="light"?"sqlviz-light":"sqlviz-dark",minimap:{enabled:!1},fontSize:13,fontFamily:"'JetBrains Mono', 'Cascadia Code', 'Fira Code', 'Consolas', monospace",lineNumbers:"on",scrollBeyondLastLine:!1,wordWrap:"off",tabSize:4,renderLineHighlight:"line",padding:{top:12,bottom:12},folding:!1,lineNumbersMinChars:3,glyphMargin:!1,overviewRulerLanes:0}),r.addCommand(y.KeyMod.CtrlCmd|y.KeyCode.Enter,()=>{var P;return(P=s.onRun)==null?void 0:P.call(s)}),r.addCommand(y.KeyMod.CtrlCmd|y.KeyCode.KeyS,()=>{var P;return(P=s.onRun)==null?void 0:P.call(s)}),r.onDidChangeModelContent(()=>{M=!0,u(r.getValue()),M=!1}),zt.set({focusStatement(P){if(!r)return;const $=r.getModel();if(!$)return;const L=r.getValue();let B=0;if(P>0){let k=0;for(let K=0;K<L.length;K++)if(L[K]===";"&&(k++,k===P)){B=K+1;break}for(;B<L.length&&(L[B]===`
`||L[B]==="\r"||L[B]===" ");)B++}const T=$.getPositionAt(B);r.revealLineInCenter(T.lineNumber),r.setPosition(T),r.focus()}}),d=y,v(b,!0),requestAnimationFrame(()=>{r==null||r.layout(),r==null||r.focus()})}catch(y){console.error("[SQLEditor] Monaco init failed:",y),v(b,!0)}}),ia(()=>{zt.set({}),r==null||r.dispose(),r=null}),lt(()=>{if(r&&!M&&r.getValue()!==u()){const y=r.getPosition();r.setValue(u()),y&&r.setPosition(y)}}),lt(()=>{r&&r.updateOptions({readOnly:h()})}),lt(()=>{!e(b)||!d||!r||d.editor.setTheme(_()==="light"?"sqlviz-light":"sqlviz-dark")});var E=ps(),R=i(E);{var q=y=>{var P=fs();g(y,P)};I(R,y=>{e(b)||y(q)})}var H=c(R,2);let D;Ca(H,y=>w=y,()=>w),n(E),O(()=>D=Q(H,1,"editor-container svelte-1dhf0v9",null,D,{hidden:!e(b)})),g(f,E),Je()}const Jt=At({});var bs=C('<span class="dash-name svelte-1uha8ag"> </span>'),ys=C('<form class="new-dash-form svelte-1uha8ag"><input class="new-dash-input svelte-1uha8ag" placeholder="Dashboard name"/> <button type="submit" class="new-dash-confirm svelte-1uha8ag">Create</button> <button type="button" class="new-dash-cancel svelte-1uha8ag">✕</button></form>'),ws=C('<button class="new-dash-btn svelte-1uha8ag">+ New</button>'),$s=C('<button title="Dashboard Score"> </button>'),ks=C('<div class="error-chip svelte-1uha8ag"><span>✕</span> <span class="error-text svelte-1uha8ag"> </span></div>'),xs=C('<span class="exec-inline svelte-1uha8ag"> </span>'),Cs=C('<div class="editor-section svelte-1uha8ag"><div class="editor-toolbar svelte-1uha8ag"><button class="run-btn svelte-1uha8ag"><span>▶</span> </button> <kbd class="shortcut svelte-1uha8ag">Ctrl+Enter</kbd> <!></div> <div class="editor-wrapper svelte-1uha8ag"><!></div></div>'),Ms=C('<div class="state-msg svelte-1uha8ag"><span class="spinner svelte-1uha8ag">⟳</span> <span> </span></div>'),Ss=C('<p class="hint svelte-1uha8ag">Separate multiple queries with <code class="svelte-1uha8ag">;</code> — each becomes a panel</p>'),Ns=C('<div class="empty-state svelte-1uha8ag"><div class="empty-arrow svelte-1uha8ag">⬇</div> <p class="svelte-1uha8ag"> </p> <!></div>'),Ts=C('<div class="toast svelte-1uha8ag" role="status" aria-live="polite"> </div>'),Es=C('<div class="app-shell svelte-1uha8ag"><header class="app-bar svelte-1uha8ag"><div class="bar-left svelte-1uha8ag"><span class="app-logo svelte-1uha8ag">SQLviz</span> <!> <!></div> <div class="bar-right svelte-1uha8ag"><!> <div class="mode-toggle svelte-1uha8ag" role="group" aria-label="Dashboard mode"><button>Preview</button> <button>Edit</button></div> <button class="theme-btn svelte-1uha8ag"> </button></div></header> <div class="app-body svelte-1uha8ag"><!> <div class="app-main svelte-1uha8ag"><!> <!> <div><!></div></div> <!></div></div> <!> <!>',1);function js(f,s){Ye(s,!0);const u=()=>bt(zt,"$editorRef",w),h=()=>bt(Jt,"$filterValues",w),_=()=>bt(pt,"$editMode",w),[w,r]=ea();let d=G(""),b=G(null),M=G(!1),E=G(null),R=G(null),q=G("dark");function H(){v(q,e(q)==="dark"?"light":"dark",!0),e(q)==="light"?document.documentElement.dataset.theme="light":delete document.documentElement.dataset.theme,localStorage.setItem("sqlviz-theme",e(q))}let D=G(null),y=G(it([])),P=G(it([])),$=G(it([])),L=G(!1),B=G(it([])),T=G(!1),k=G(""),K=G(null),me=0;const be=W(()=>e(b)!==null&&e(b).rows.length>0),De=W(()=>e(B).length>=2),Se=W(()=>e(B).find(t=>t.id===e(D))??null),Be=W(()=>{var t;return((t=e(b))==null?void 0:t.utility_score)!=null?Math.round(e(b).utility_score*100):null}),qe=W(()=>{const t=new Set,a=[];for(const o of e($))for(const l of o.inference_result.filter_controls)t.has(l.variable)||(t.add(l.variable),a.push(l));return a}),He=W(()=>e(qe).length>0);let de=0;async function V(t,a){const o=await fetch(t,{method:"POST",headers:a!==void 0?{"Content-Type":"application/json"}:{},body:a!==void 0?JSON.stringify(a):void 0});if(!o.ok){const l=await o.json().catch(()=>null);throw new Error((l==null?void 0:l.detail)??`${o.status} ${o.statusText}`)}return o.json()}async function ve(t,a){const o=await fetch(t,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify(a)});if(!o.ok){const l=await o.json().catch(()=>null);throw new Error((l==null?void 0:l.detail)??`${o.status} ${o.statusText}`)}return o.json()}async function X(t){const a=t.map(m=>({panel_id:m.panel_id,inference_result:m.inference_result})),o=await V("/api/v1/compose",a),l=new Map(t.map(m=>[m.panel_id,m.data]));return{...o,rows:o.rows.map(m=>({panels:m.panels.map(p=>({...p,data:l.get(p.panel_id)??[]}))}))}}Xt(async()=>{localStorage.getItem("sqlviz-theme")==="light"&&(v(q,"light"),document.documentElement.dataset.theme="light");const a=await fetch("/api/v1/auth/me");if(a.status===401){await Na("/login");return}const o=await a.json();o.demo&&pt.set(!0);try{const l=await fetch("/api/v1/dashboards").then(p=>p.json());if(v(B,l,!0),l.length===0){if(o.demo){const{sql:p}=await fetch("/api/v1/demo/sql").then(N=>N.json());v(d,p,!0),j()}return}v(D,l[0].id,!0);const m=await fetch(`/api/v1/panels?dashboard_id=${e(D)}`).then(p=>p.json());if(m.length===0)return;m.sort((p,N)=>p.sort_order-N.sort_order),v(y,m.map(p=>p.id),!0),v(P,m.map(p=>p.sql_content),!0),v(d,e(P).join(`;

`),!0)}catch{}});async function j(){if(e(M))return;const t=e(d).split(";").map(l=>l.trim()).filter(l=>l.length>0);if(t.length===0){v(R,'No SQL statements found. Write at least one query separated by ";".');return}v(M,!0),v(R,null);let a=e(D);const o=[...e(y)];try{a||(a=(await V("/api/v1/dashboards",{name:"My Dashboard",sort_order:0})).id,v(D,a,!0));const l=[],m=[];for(let p=0;p<t.length;p++){const N=t[p];v(E,`Statement ${p+1} / ${t.length}…`);let F;o[p]?(await ve(`/api/v1/panels/${o[p]}`,{sql_content:N,sort_order:p}),F=o[p]):F=(await V("/api/v1/panels",{dashboard_id:a,name:`Panel ${p+1}`,sql_content:N,sort_order:p})).id,m.push(F);const U=await V(`/api/v1/panels/${F}/execute`);l.push({panel_id:F,...U})}if(e(D)!==a){v(E,null);return}v(y,m,!0),v(P,t,!0),v($,l,!0),v(E,"Composing layout…"),v(b,await X(l),!0),v(E,null);try{v(B,await fetch("/api/v1/dashboards").then(p=>p.json()),!0)}catch{}}catch(l){v(R,l instanceof Error?l.message:String(l),!0),v(E,null)}finally{v(M,!1)}}async function ge(t){const a=e(y).indexOf(t);if(a<0)return;try{await fetch(`/api/v1/panels/${t}`,{method:"DELETE"})}catch{le("Delete failed — check the API server.");return}const o=e($).filter((p,N)=>N!==a),l=e(y).filter((p,N)=>N!==a),m=e(P).filter((p,N)=>N!==a);if(v($,o,!0),v(y,l,!0),v(P,m,!0),v(d,m.join(`;

`),!0),o.length===0){v(b,null);return}try{v(b,await X(o),!0)}catch(p){le(p instanceof Error?p.message:"Compose failed after delete.")}}function fe(t){var o,l;const a=e(y).indexOf(t);a<0||(l=(o=u()).focusStatement)==null||l.call(o,a)}function Ne(t){const a=e($).find(o=>o.panel_id===t);if(!a){le("Run the dashboard first to see explainability data.");return}qt.set(a)}async function ye(){const t=e(k).trim()||"New Dashboard";v(T,!1),v(k,"");try{const a=await V("/api/v1/dashboards",{name:t,sort_order:e(B).length});v(B,await fetch("/api/v1/dashboards").then(o=>o.json()),!0),v(D,a.id,!0),v(y,[],!0),v(P,[],!0),v(d,""),v($,[],!0),v(b,null)}catch(a){le(a instanceof Error?a.message:"Could not create dashboard.")}}function ue(){v(T,!1),v(k,"")}async function ie(t){if(!(t===e(D)||e(M)))try{const a=await fetch(`/api/v1/panels?dashboard_id=${t}`).then(o=>o.json());a.sort((o,l)=>o.sort_order-l.sort_order),v(D,t,!0),v(y,a.map(o=>o.id),!0),v(P,a.map(o=>o.sql_content),!0),v(d,e(P).join(`;

`),!0),v($,[],!0),v(b,null),a.length>0&&j()}catch(a){le(a instanceof Error?a.message:"Could not load dashboard.")}}async function Te(t,a){try{await ve(`/api/v1/panels/${t}/override`,{field_name:"chart_type",user_value:a});const o=await V(`/api/v1/panels/${t}/execute`);v($,e($).map(l=>l.panel_id===t?{panel_id:t,inference_result:o.inference_result,data:o.data}:l),!0),v(b,await X(e($)),!0)}catch(o){le(o instanceof Error?o.message:"Chart override failed.")}}function we(t,a){e(b)&&v(b,{...e(b),rows:e(b).rows.map(o=>({panels:o.panels.map(l=>l.panel_id!==t?l:{...l,final_col_span:a??l.inference_result.col_span})}))},!0)}function Le(t,a){e(b)&&v(b,{...e(b),rows:e(b).rows.map(o=>({panels:o.panels.map(l=>l.panel_id!==t?l:{...l,inference_result:{...l.inference_result,panel_height_px:a??l.inference_result.panel_height_px}})}))},!0)}async function he(t,a){const o=[...e($)];let l=!1;for(let m=0;m<e($).length;m++){const N=e($)[m].inference_result.filter_controls.flatMap(A=>A.variable.split(",").map(ce=>ce.trim()));if(!N.includes(t)||!N.every(A=>{const ce=a[A];return ce!==void 0&&ce!==""&&ce!==null}))continue;const U=Object.fromEntries(N.map(A=>[A,a[A]])),Z=e(y)[m];try{const A=await V(`/api/v1/panels/${Z}/execute`,{variables:U});o[m]={panel_id:Z,...A},l=!0}catch{}}if(l){v($,o,!0);try{v(b,await X(o),!0)}catch{}}}function Ee(t,a){Jt.update(o=>({...o,[t]:a})),clearTimeout(de),de=window.setTimeout(()=>{const o={...h(),[t]:a};he(t,o)},350)}function le(t,a=3500){v(K,t,!0),clearTimeout(me),me=window.setTimeout(()=>{v(K,null)},a)}var Ie=Es(),ae=z(Ie),se=i(ae),$e=i(se),ct=c(i($e),2);{var $t=t=>{var a=bs(),o=i(a,!0);n(a),O(()=>{Qe(a,"title",e(Se).name),S(o,e(Se).name)}),g(t,a)};I(ct,t=>{e(Se)&&t($t)})}var Xe=c(ct,2);{var Ze=t=>{var a=ys(),o=i(a);Ma(o),ka(o,!0);var l=c(o,4);n(a),Zt("submit",a,m=>{m.preventDefault(),ye()}),ee("keydown",o,m=>{m.key==="Escape"&&ue()}),Sa(o,()=>e(k),m=>v(k,m)),ee("click",l,ue),g(t,a)},et=t=>{var a=ws();O(()=>{a.disabled=e(M),Qe(a,"title",e(M)?"Wait for current run to finish":"New dashboard")}),ee("click",a,()=>{v(T,!0)}),g(t,a)};I(Xe,t=>{e(T)?t(Ze):t(et,-1)})}n($e);var dt=c($e,2),vt=i(dt);{var kt=t=>{var a=$s();let o;var l=i(a);n(a),O(()=>{o=Q(a,1,"score-btn svelte-1uha8ag",null,o,{active:e(L)}),S(l,`Score${e(Be)!=null?`: ${e(Be)}`:""}
                    ${e(L)?"▼":"▲"}`)}),ee("click",a,()=>v(L,!e(L))),g(t,a)};I(vt,t=>{_()&&t(kt)})}var tt=c(vt,2),at=i(tt);let je;var Fe=c(at,2);let Ue;n(tt);var ze=c(tt,2),st=i(ze,!0);n(ze),n(dt),n(se);var ut=c(se,2),ht=i(ut);{var xt=t=>{ts(t,{get items(){return e(B)},get activeId(){return e(D)},onSelect:ie})};I(ht,t=>{e(De)&&t(xt)})}var We=c(ht,2),Ve=i(We);{var nt=t=>{Ta(t,{get controls(){return e(qe)},get filterVals(){return h()},onChange:Ee})};I(Ve,t=>{e(He)&&t(nt)})}var Ge=c(Ve,2);{var Ct=t=>{var a=Cs(),o=i(a),l=i(o),m=i(l);let p;var N=c(m);n(l);var F=c(l,4);{var U=ne=>{var _e=ks(),Re=c(i(_e),2),na=i(Re,!0);n(Re),n(_e),O(()=>{Qe(_e,"title",e(R)),S(na,e(R))}),g(ne,_e)},Z=ne=>{var _e=xs(),Re=i(_e,!0);n(_e),O(()=>S(Re,e(E))),g(ne,_e)};I(F,ne=>{e(R)?ne(U):e(M)&&e(E)&&e(be)&&ne(Z,1)})}n(o);var A=c(o,2),ce=i(A);ms(ce,{onRun:j,get disabled(){return e(M)},get theme(){return e(q)},get value(){return e(d)},set value(ne){v(d,ne,!0)}}),n(A),n(a),O(()=>{l.disabled=e(M),p=Q(m,1,"run-icon svelte-1uha8ag",null,p,{spinning:e(M)}),S(N,` ${(e(M)?e(E)??"Running…":"Run")??""}`)}),ee("click",l,j),g(t,a)};I(Ge,t=>{_()&&t(Ct)})}var Ae=c(Ge,2);let _t;var rt=i(Ae);{var Mt=t=>{var a=Ms(),o=c(i(a),2),l=i(o,!0);n(o),n(a),O(()=>S(l,e(E)??"Executing…")),g(t,a)},ot=t=>{var a=Ns(),o=c(i(a),2),l=i(o,!0);n(o);var m=c(o,2);{var p=N=>{var F=Ss();g(N,F)};I(m,N=>{_()&&N(p)})}n(a),O(()=>S(l,_()?"Press Ctrl+Enter to run and see results here":"Switch to Edit mode to write SQL and create panels")),g(t,a)},St=t=>{Ea(t,{get layout(){return e(b)},onEditSQL:fe,onExplain:Ne,onDelete:ge,onChartOverride:Te,onWidthOverride:we,onHeightOverride:Le})};I(rt,t=>{e(M)&&!e(be)?t(Mt):e(be)?e(b)&&t(St,2):t(ot,1)})}n(Ae),n(We);var gt=c(We,2);{var Nt=t=>{Ua(t,{get layout(){return e(b)},onClose:()=>v(L,!1)})};I(gt,t=>{_()&&e(L)&&e(b)&&t(Nt)})}n(ut),n(ae);var ft=c(ae,2);{var Tt=t=>{var a=Ts(),o=i(a,!0);n(a),O(()=>S(o,e(K))),g(t,a)};I(ft,t=>{e(K)&&t(Tt)})}var x=c(ft,2);gs(x,{}),O(()=>{je=Q(at,1,"mode-btn svelte-1uha8ag",null,je,{active:!_()}),Ue=Q(Fe,1,"mode-btn svelte-1uha8ag",null,Ue,{active:_()}),Qe(ze,"aria-label",e(q)==="dark"?"Switch to light mode":"Switch to dark mode"),Qe(ze,"title",e(q)==="dark"?"Light mode":"Dark mode"),S(st,e(q)==="dark"?"☀":"☾"),_t=Q(Ae,1,"dashboard-area svelte-1uha8ag",null,_t,{empty:!e(be)&&!e(M)})}),ee("click",at,()=>pt.set(!1)),ee("click",Fe,()=>pt.set(!0)),ee("click",ze,H),g(f,Ie),Je(),r()}wt(["keydown","click"]);export{js as component};
