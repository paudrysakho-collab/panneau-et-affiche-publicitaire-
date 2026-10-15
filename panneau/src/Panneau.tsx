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

const SERIF = "'Cormorant Garamond', serif";
const SANS = "'Montserrat', sans-serif";

// Bouteilles en arc : la plus grande au centre, les autres en retrait (base plus haute, plus petites, derrière).
// x = centre, h = hauteur affichée, base = bas de la bouteille, z = ordre d'empilement.
const BOUTEILLES = [
	{src: 'whisky_toki.png', ratio: 0.384, x: 172, h: 380, base: 988, z: 1},
	{src: 'blacailloux.png', ratio: 0.223, x: 293, h: 486, base: 1002, z: 2},
	{src: 'gragnos_lou_daro.png', ratio: 0.258, x: 418, h: 530, base: 1016, z: 3},
	{src: 'chateauneuf.png', ratio: 0.258, x: 552, h: 570, base: 1030, z: 5},
	{src: 'balac.png', ratio: 0.242, x: 690, h: 556, base: 1030, z: 4},
	{src: 'frezier.png', ratio: 0.266, x: 824, h: 522, base: 1016, z: 3},
	{src: 'divin_sauvignon_0-0.png', ratio: 0.275, x: 952, h: 482, base: 1002, z: 2},
	{src: 'rhum_la_favorite.png', ratio: 0.317, x: 1072, h: 418, base: 988, z: 1},
];

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

const Icone: React.FC<{nom: string}> = ({nom}) => {
	const trait = {fill: 'none', stroke: C.or, strokeWidth: 1.6, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const};
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

const Produit: React.FC<{src: string; ratio: number; x: number; h: number; base: number; reflet: number; z?: number}> = ({src, ratio, x, h, base, reflet, z = 1}) => {
	const l = h * ratio;
	return (
		<>
			<div
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
			/>
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

const BlocTexte: React.FC<{bloc: Bloc}> = ({bloc}) => (
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
							color: C[s.couleur] ?? s.couleur,
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

export const Panneau: React.FC<{texte?: boolean}> = ({texte = true}) => {
	return (
		<AbsoluteFill style={{background: C.encre, color: C.creme, fontFamily: SANS, overflow: 'hidden', fontVariantNumeric: 'lining-nums'}}>
			<Polices />

			{/* Fond : halo lie-de-vin derrière les produits */}
			<AbsoluteFill
				style={{
					background: `radial-gradient(ellipse 760px 700px at 50% 47%, ${C.vin} 0%, rgba(74,15,31,0.55) 45%, rgba(20,16,18,0) 80%)`,
				}}
			/>
			<AbsoluteFill
				style={{
					background: 'radial-gradient(ellipse 420px 360px at 50% 52%, rgba(207,165,72,0.16), rgba(207,165,72,0) 75%)',
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
			<div style={{position: 'absolute', inset: 26, border: `1.5px solid ${C.or}`, opacity: 0.85}} />
			<div style={{position: 'absolute', inset: 34, border: `0.75px solid ${C.or}`, opacity: 0.45}} />

			{texte && (
				<Img src={staticFile('logo_cave71_transparent.png')} style={{position: 'absolute', top: 112, left: (LARGEUR - 640) / 2, width: 640}} />
			)}

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
				<Produit key={b.src} {...b} reflet={0.2} />
			))}
			{PREMIER_PLAN.map((t) => (
				<Produit key={t.src} {...t} base={PREMIER_PLAN_Y} reflet={0} z={10} />
			))}

			{/* Filets autour du titre des services */}
			<div style={{position: 'absolute', top: 1305, left: 404, width: 120, height: 1, background: C.or, opacity: 0.6}} />
			<div style={{position: 'absolute', top: 1305, left: 716, width: 120, height: 1, background: C.or, opacity: 0.6}} />

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
						border: `1px solid rgba(207,165,72,0.6)`,
						display: 'flex',
						alignItems: 'center',
						justifyContent: 'center',
					}}
				>
					<Icone nom={i.nom} />
				</div>
			))}

			{/* Pied */}
			<div style={{position: 'absolute', top: 1484, left: 90, right: 90, height: 1, background: `linear-gradient(to right, rgba(207,165,72,0), ${C.or}, rgba(207,165,72,0))`}} />
			<div style={{position: 'absolute', top: 1508, left: 1044, background: C.creme, padding: 7, borderRadius: 4}}>
				<Img src={staticFile('qr_cave71.svg')} style={{width: 92, height: 92, display: 'block'}} />
			</div>

			{texte && (textes.blocs as Bloc[]).map((b) => <BlocTexte key={b.id} bloc={b} />)}
		</AbsoluteFill>
	);
};
