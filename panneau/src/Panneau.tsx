import React, {useEffect, useState} from 'react';
import {AbsoluteFill, Img, continueRender, delayRender, staticFile} from 'remotion';
import textes from './textes.json';

export const LARGEUR = 1240;
export const HAUTEUR = 1754;

export const C: Record<string, string> = {
	encre: '#141012',
	vin: '#4a0f1f',
	bordeaux: '#7d1530',
	or: '#cfa548',
	orPale: '#e6cf98',
	creme: '#f4ece0',
	cremeDoux: 'rgba(244,236,224,0.72)',
};

// Palette de la version claire (fond blanc chaud de la photo studio) : mêmes noms, autres valeurs.
export const CLAIR: Record<string, string> = {
	encre: '#f3ebe1',
	vin: '#fbf7f1',
	bordeaux: '#7d1530',
	or: '#a77a26',
	orPale: '#7d1530',
	creme: '#2a1619',
	cremeDoux: 'rgba(42,22,25,0.68)',
};

const SERIF = "'Cormorant Garamond', serif";
const SANS = "'Montserrat', sans-serif";

// Groupe des 8 bouteilles composé par script (tools/compo_bouteilles.py) : étiquettes d'origine, deux rangs en quinconce.
// base = bas de l'image ; les bouteilles avant posent ~52 px plus haut (ombres portées dessous), soit sur l'étagère.
const BOUTEILLES = [{src: 'bouteilles_groupe.png', ratio: 2.005, x: 620, h: 539, base: 1082, z: 2}];

// Premier plan : composition jus de cépage + terrines + chocolats (détourée), centrée.
const PREMIER_PLAN = [{src: 'premier_plan_groupe.png', ratio: 1.507, x: 620, h: 345}];

const ETAGERE_Y = 1030;
const PREMIER_PLAN_Y = 1268;

// Icônes des services, alignées sur les blocs service-1..5 de textes.json.
const ICONES = [
	{nom: 'cadeau', x: 90, y: 1340},
	{nom: 'verres', x: 443, y: 1340},
	{nom: 'bouteille', x: 796, y: 1340},
	{nom: 'carte', x: 267, y: 1412},
	{nom: 'alliances', x: 620, y: 1412},
];

const Icone: React.FC<{nom: string; couleur: string}> = ({nom, couleur}) => {
	const trait = {fill: 'none', stroke: couleur, strokeWidth: 1.6, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const};
	return (
		<svg width={34} height={34} viewBox="0 0 32 32">
			{nom === 'cadeau' && (
				<g {...trait}>
					<rect x={5} y={13} width={22} height={14} />
					<rect x={3.5} y={9} width={25} height={4} />
					<path d="M16 9v18M16 9c-2-5-8-5-7-1 1 2 5 1 7 1zM16 9c2-5 8-5 7-1-1 2-5 1-7 1z" />
				</g>
			)}
			{nom === 'verres' && (
				<g {...trait}>
					<path d="M6 4h8c0 6-1.5 9-4 9S6 10 6 4zM10 13v11M6.5 24h7" />
					<path d="M18 4h8c0 6-1.5 9-4 9s-4-3-4-9zM22 13v11M18.5 24h7" />
				</g>
			)}
			{nom === 'bouteille' && (
				<g {...trait}>
					<path d="M14 3h4v6c3 1.5 4 4 4 7v12a1 1 0 0 1-1 1h-10a1 1 0 0 1-1-1V16c0-3 1-5.5 4-7z" />
					<rect x={11.5} y={17} width={9} height={7} />
				</g>
			)}
			{nom === 'carte' && (
				<g {...trait}>
					<path d="M7 4h15l4 4v20H7z" />
					<path d="M11 11h11M11 15h11M11 19h8M11 23h6" />
				</g>
			)}
			{nom === 'alliances' && (
				<g {...trait}>
					<circle cx={12} cy={19} r={7} />
					<circle cx={20} cy={19} r={7} />
					<path d="M18 6l2-3 2 3-2 2z" />
				</g>
			)}
		</svg>
	);
};

const Polices: React.FC = () => {
	const [handle] = useState(() => delayRender('Chargement des polices'));
	useEffect(() => {
		const polices = [
			new FontFace('Cormorant Garamond', `url(${staticFile('fonts/CormorantGaramond.ttf')})`, {weight: '300 700'}),
			new FontFace('Cormorant Garamond', `url(${staticFile('fonts/CormorantGaramond-Italic.ttf')})`, {weight: '300 700', style: 'italic'}),
			new FontFace('Montserrat', `url(${staticFile('fonts/Montserrat.ttf')})`, {weight: '100 900'}),
		];
		Promise.all(polices.map((p) => p.load()))
			.then((chargees) => {
				chargees.forEach((p) => (document.fonts as unknown as {add: (f: FontFace) => void}).add(p));
				continueRender(handle);
			})
			.catch((e) => {
				console.error(e);
				continueRender(handle);
			});
	}, [handle]);
	return null;
};

const Produit: React.FC<{src: string; ratio: number; x: number; h: number; base: number; reflet: number; z?: number; ombre?: boolean}> = ({src, ratio, x, h, base, reflet, z = 1, ombre = true}) => {
	const l = h * ratio;
	return (
		<>
			{ombre && <div
				style={{
					position: 'absolute',
					left: x - l * 0.62,
					top: base - 9,
					width: l * 1.24,
					height: 18,
					borderRadius: '50%',
					zIndex: z,
					background: 'radial-gradient(closest-side, rgba(0,0,0,0.75), rgba(0,0,0,0))',
				}}
			/>}
			<Img
				src={staticFile(`produits/${src}`)}
				style={{
					position: 'absolute',
					left: x - l / 2,
					top: base,
					width: l,
					height: h,
					zIndex: 0,
					transform: 'scaleY(-1)',
					opacity: reflet,
					WebkitMaskImage: 'linear-gradient(to top, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 22%)',
					maskImage: 'linear-gradient(to top, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 22%)',
				}}
			/>
			<Img
				src={staticFile(`produits/${src}`)}
				style={{
					position: 'absolute',
					left: x - l / 2,
					top: base - h,
					width: l,
					height: h,
					zIndex: z,
					filter: 'drop-shadow(6px 10px 16px rgba(0,0,0,0.55))',
				}}
			/>
		</>
	);
};

type Segment = {t: string; police: string; taille: number; graisse?: number; italique?: boolean; couleur: string; espacement?: number};
type Bloc = {id: string; x: number; y: number; w: number; align: string; interligne?: number; lignes: Segment[][]};

const BlocTexte: React.FC<{bloc: Bloc; K: Record<string, string>}> = ({bloc, K}) => (
	<div
		style={{
			position: 'absolute',
			left: bloc.x,
			top: bloc.y,
			width: bloc.w,
			textAlign: bloc.align as React.CSSProperties['textAlign'],
			lineHeight: bloc.interligne ?? 1.2,
			zIndex: 20,
		}}
	>
		{bloc.lignes.map((ligne, i) => (
			<div key={i} style={{whiteSpace: 'nowrap'}}>
				{ligne.map((s, j) => (
					<span
						key={j}
						style={{
							fontFamily: s.police === 'serif' ? SERIF : SANS,
							fontSize: s.taille,
							fontWeight: s.graisse ?? 400,
							fontStyle: s.italique ? 'italic' : 'normal',
							color: K[s.couleur] ?? s.couleur,
							letterSpacing: s.espacement ?? 0,
						}}
					>
						{s.t}
					</span>
				))}
			</div>
		))}
	</div>
);

// Mode « vitrine » : la photo studio Gemini (bouteilles + terrines + chocolat) dans une fenêtre en arche,
// à la place de l'étagère et des produits détourés.
const VITRINE = {src: 'vitrine_gemini.jpg', ratio: 2000 / 1356, x: 92, y: 500, w: 1056, fleche: 200};

const Vitrine: React.FC<{clair?: boolean}> = ({clair = false}) => {
	const {src, ratio, x, y, w, fleche} = VITRINE;
	const h = w / ratio;
	if (clair) {
		// Version claire : pas de cadre, la photo se fond dans le fond par des bords en dégradé.
		const fondu = 'linear-gradient(to right, transparent, black 5%, black 95%, transparent), linear-gradient(to bottom, transparent, black 18%, black 94%, transparent)';
		return (
			<Img
				src={staticFile(`produits/${src}`)}
				style={{position: 'absolute', left: x - 20, top: y - 40, width: w + 40, height: (w + 40) / ratio, WebkitMaskImage: fondu, maskImage: fondu, WebkitMaskComposite: 'source-in', maskComposite: 'intersect'}}
			/>
		);
	}
	const arche = (dx: number) =>
		`M ${-dx} ${h + dx} L ${-dx} ${fleche} A ${w / 2 + dx} ${fleche + dx} 0 0 1 ${w + dx} ${fleche} L ${w + dx} ${h + dx} Z`;
	return (
		<>
			<div style={{position: 'absolute', left: x, top: y, width: w, height: h, clipPath: `path('${arche(0)}')`, boxShadow: '0 0 80px rgba(0,0,0,0.6)'}}>
				<Img src={staticFile(`produits/${src}`)} style={{width: w, height: h, display: 'block'}} />
				{/* fondu discret vers le bas pour lier la photo au fond sombre */}
				<div style={{position: 'absolute', inset: 0, background: 'linear-gradient(to bottom, rgba(20,16,18,0) 88%, rgba(20,16,18,0.35))'}} />
			</div>
			<svg width={w + 40} height={h + 40} style={{position: 'absolute', left: x - 20, top: y - 20, overflow: 'visible'}}>
				<g transform="translate(20 20)">
					<path d={arche(6)} fill="none" stroke={C.or} strokeWidth={1.6} opacity={0.9} />
					<path d={arche(13)} fill="none" stroke={C.or} strokeWidth={0.7} opacity={0.5} />
				</g>
			</svg>
		</>
	);
};

export const Panneau: React.FC<{texte?: boolean; vitrine?: boolean; clair?: boolean}> = ({texte = true, vitrine = false, clair = false}) => {
	const K = clair ? CLAIR : C;
	return (
		<AbsoluteFill style={{background: K.encre, color: K.creme, fontFamily: SANS, overflow: 'hidden', fontVariantNumeric: 'lining-nums'}}>
			<Polices />

			{/* Fond : halo lie-de-vin derrière les produits */}
			<AbsoluteFill
				style={{
					background: clair
						? 'radial-gradient(ellipse 900px 900px at 50% 45%, #fbf7f1 0%, #f5eee5 45%, rgba(234,221,204,0.9) 100%)'
						: `radial-gradient(ellipse 760px 700px at 50% 47%, ${C.vin} 0%, rgba(74,15,31,0.55) 45%, rgba(20,16,18,0) 80%)`,
				}}
			/>
			<AbsoluteFill
				style={{
					background: clair ? 'none' : 'radial-gradient(ellipse 420px 360px at 50% 52%, rgba(207,165,72,0.16), rgba(207,165,72,0) 75%)',
				}}
			/>

			{/* Grain léger */}
			<svg width={LARGEUR} height={HAUTEUR} style={{position: 'absolute', inset: 0, opacity: 0.07, mixBlendMode: 'overlay'}}>
				<filter id="grain">
					<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} stitchTiles="stitch" />
				</filter>
				<rect width="100%" height="100%" filter="url(#grain)" />
			</svg>

			{/* Double filet doré */}
			<div style={{position: 'absolute', inset: 26, border: `1.5px solid ${K.or}`, opacity: 0.85}} />
			<div style={{position: 'absolute', inset: 34, border: `0.75px solid ${K.or}`, opacity: 0.45}} />

			{texte && (
				<Img src={staticFile(clair ? 'logo_cave71_sombre.png' : 'logo_cave71_transparent.png')} style={{position: 'absolute', top: 112, left: (LARGEUR - 640) / 2, width: 640}} />
			)}

			{vitrine ? (
				<Vitrine clair={clair} />
			) : (
				<>
			{/* Voûte de cave */}
			<svg width={LARGEUR} height={HAUTEUR} style={{position: 'absolute', inset: 0}}>
				<defs>
					<linearGradient id="voute" x1="0" y1="0" x2="0" y2="1">
						<stop offset="0" stopColor={C.or} stopOpacity={0.9} />
						<stop offset="1" stopColor={C.or} stopOpacity={0.15} />
					</linearGradient>
				</defs>
				<path d={`M 66 ${ETAGERE_Y} L 66 760 A 554 330 0 0 1 1174 760 L 1174 ${ETAGERE_Y}`} fill="none" stroke="url(#voute)" strokeWidth={1.6} />
				<path d={`M 80 ${ETAGERE_Y} L 80 762 A 540 318 0 0 1 1160 762 L 1160 ${ETAGERE_Y}`} fill="none" stroke="url(#voute)" strokeWidth={0.7} opacity={0.6} />
			</svg>

			{/* Étagère : plateau en profondeur + chant avant */}
			<div
				style={{
					position: 'absolute',
					left: 60,
					right: 60,
					top: ETAGERE_Y - 62,
					height: 62,
					background: 'linear-gradient(to bottom, rgba(90,30,44,0), rgba(110,40,56,0.45))',
					WebkitMaskImage: 'linear-gradient(to right, transparent, black 18%, black 82%, transparent)',
					maskImage: 'linear-gradient(to right, transparent, black 18%, black 82%, transparent)',
				}}
			/>
			<div
				style={{
					position: 'absolute',
					left: 60,
					right: 60,
					top: ETAGERE_Y,
					height: 150,
					background: 'linear-gradient(to bottom, rgba(90,30,44,0.6), rgba(20,16,18,0) 90%)',
					WebkitMaskImage: 'linear-gradient(to right, transparent, black 18%, black 82%, transparent)',
					maskImage: 'linear-gradient(to right, transparent, black 18%, black 82%, transparent)',
				}}
			/>
			<div
				style={{
					position: 'absolute',
					left: 60,
					right: 60,
					top: ETAGERE_Y,
					height: 1,
					background: 'linear-gradient(to right, rgba(230,207,152,0), rgba(230,207,152,0.7) 25%, rgba(230,207,152,0.7) 75%, rgba(230,207,152,0))',
				}}
			/>

			{BOUTEILLES.map((b) => (
				<Produit key={b.src} {...b} reflet={0} ombre={false} />
			))}
			{PREMIER_PLAN.map((t) => (
				<Produit key={t.src} {...t} base={PREMIER_PLAN_Y} reflet={0} z={10} />
			))}

				</>
			)}

			{/* Filets autour du titre des services */}
			<div style={{position: 'absolute', top: 1305, left: 404, width: 120, height: 1, background: K.or, opacity: 0.6}} />
			<div style={{position: 'absolute', top: 1305, left: 716, width: 120, height: 1, background: K.or, opacity: 0.6}} />

			{ICONES.map((i) => (
				<div
					key={i.nom}
					style={{
						position: 'absolute',
						left: i.x,
						top: i.y,
						width: 58,
						height: 58,
						borderRadius: '50%',
						border: `1px solid ${K.or}`,
						opacity: 0.95,
						display: 'flex',
						alignItems: 'center',
						justifyContent: 'center',
					}}
				>
					<Icone nom={i.nom} couleur={K.or} />
				</div>
			))}

			{/* Pied */}
			<div style={{position: 'absolute', top: 1484, left: 90, right: 90, height: 1, background: `linear-gradient(to right, transparent, ${K.or}, transparent)`}} />
			<div style={{position: 'absolute', top: 1508, left: 1044, background: clair ? '#fff' : C.creme, padding: 7, borderRadius: 4}}>
				<Img src={staticFile('qr_cave71.svg')} style={{width: 92, height: 92, display: 'block'}} />
			</div>

			{texte && (textes.blocs as Bloc[]).map((b) => <BlocTexte key={b.id} bloc={b} K={K} />)}
		</AbsoluteFill>
	);
};
