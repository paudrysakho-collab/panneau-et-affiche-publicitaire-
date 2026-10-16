import React, {useEffect, useState} from 'react';
import {AbsoluteFill, Img, continueRender, delayRender, staticFile} from 'remotion';
import textes from './textes.json';

// Stop-trottoir A1 portrait (594 x 841 mm). Toile 1240 x 1754 px, export x2.829 = 3508 x 4962 px (150 dpi).
// Les textes (src/textes.json) sont volontairement grands : lisibles à quelques mètres sur le trottoir.
export const LARGEUR = 1240;
export const HAUTEUR = 1754;

// Version sombre : le lie-de-vin de la photo studio, prolongé sur toute l'affiche.
export const C: Record<string, string> = {
	encre: '#0f0405',
	vin: '#4a1a20',
	bordeaux: '#7d1530',
	or: '#cfa548',
	orPale: '#e6cf98',
	creme: '#f4ece0',
	cremeDoux: 'rgba(244,236,224,0.72)',
};

// Version claire : le blanc chaud de la photo studio. Mêmes noms de couleurs, autres valeurs.
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

// Photo studio Gemini (bouteilles, jus, terrines, chocolat), fondue dans le fond par des bords en dégradé.
const PHOTO = {x: 20, y: 408, w: 1200, ratio: 2000 / 1116};

// Icônes des services, à gauche des blocs service-1..5 de textes.json.
const ICONES = [
	{nom: 'cadeau', x: 58, y: 1140},
	{nom: 'verres', x: 448, y: 1140},
	{nom: 'bouteille', x: 848, y: 1140},
	{nom: 'carte', x: 183, y: 1234},
	{nom: 'alliances', x: 648, y: 1234},
];

const Icone: React.FC<{nom: string; couleur: string}> = ({nom, couleur}) => {
	const trait = {fill: 'none', stroke: couleur, strokeWidth: 1.6, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const};
	return (
		<svg width={38} height={38} viewBox="0 0 32 32">
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

const Photo: React.FC<{clair: boolean}> = ({clair}) => {
	const {x, y, w, ratio} = PHOTO;
	const fondu =
		'linear-gradient(to right, transparent, black 5%, black 95%, transparent), linear-gradient(to bottom, transparent, black 10%, black 92%, transparent)';
	return (
		<Img
			src={staticFile(`produits/${clair ? 'vitrine_clair.jpg' : 'vitrine_sombre.jpg'}`)}
			style={{position: 'absolute', left: x, top: y, width: w, height: w / ratio, WebkitMaskImage: fondu, maskImage: fondu, WebkitMaskComposite: 'source-in', maskComposite: 'intersect'}}
		/>
	);
};

export const Panneau: React.FC<{texte?: boolean; clair?: boolean}> = ({texte = true, clair = false}) => {
	const K = clair ? CLAIR : C;
	const centreY = ((PHOTO.y + PHOTO.w / PHOTO.ratio / 2) / HAUTEUR) * 100;
	return (
		<AbsoluteFill style={{background: K.encre, color: K.creme, fontFamily: SANS, overflow: 'hidden', fontVariantNumeric: 'lining-nums'}}>
			<Polices />

			{/* Fond : halo assorti à celui de la photo, centré sur les produits */}
			<AbsoluteFill
				style={{
					background: clair
						? `radial-gradient(ellipse 900px 900px at 50% ${centreY}%, #fbf7f1 0%, #f5eee5 45%, rgba(234,221,204,0.9) 100%)`
						: `radial-gradient(ellipse 820px 760px at 50% ${centreY}%, ${C.vin} 0%, #2a0c10 40%, rgba(15,4,5,0) 85%)`,
				}}
			/>

			{/* Grain léger */}
			<svg width={LARGEUR} height={HAUTEUR} style={{position: 'absolute', inset: 0, opacity: 0.07, mixBlendMode: 'overlay'}}>
				<filter id="grain">
					<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} stitchTiles="stitch" />
				</filter>
				<rect width="100%" height="100%" filter="url(#grain)" />
			</svg>

			<Photo clair={clair} />

			{/* Double filet doré */}
			<div style={{position: 'absolute', inset: 26, border: `1.5px solid ${K.or}`, opacity: 0.85}} />
			<div style={{position: 'absolute', inset: 34, border: `0.75px solid ${K.or}`, opacity: 0.45}} />

			{/* Logo officiel, couleurs jamais modifiées : CAVE blanc, 71 bordeaux, sur son bloc noir. */}
			{texte && <Img src={staticFile('logo_cave71_bloc.png')} style={{position: 'absolute', top: 98, left: (LARGEUR - 760) / 2, width: 760}} />}

			{/* Filets autour du titre des services */}
			<div style={{position: 'absolute', top: 1109, left: 220, width: 220, height: 1, background: K.or, opacity: 0.7}} />
			<div style={{position: 'absolute', top: 1109, left: 800, width: 220, height: 1, background: K.or, opacity: 0.7}} />

			{ICONES.map((i) => (
				<div
					key={i.nom}
					style={{
						position: 'absolute',
						left: i.x,
						top: i.y,
						width: 64,
						height: 64,
						borderRadius: '50%',
						border: `1.2px solid ${K.or}`,
						display: 'flex',
						alignItems: 'center',
						justifyContent: 'center',
					}}
				>
					<Icone nom={i.nom} couleur={K.or} />
				</div>
			))}

			{/* Pied : grille 2 x 2 (adresse | horaires / en ligne | QR code) séparée par des filets dorés */}
			<div style={{position: 'absolute', top: 1336, left: 60, right: 60, height: 1, background: `linear-gradient(to right, transparent, ${K.or}, transparent)`}} />
			<div style={{position: 'absolute', top: 1508, left: 70, right: 70, height: 1, background: K.or, opacity: 0.35}} />
			<div style={{position: 'absolute', top: 1356, bottom: 1754 - 1660, left: 635, width: 1, background: K.or, opacity: 0.35}} />
			<div style={{position: 'absolute', top: 1524, left: 665, background: '#fff', padding: 8, borderRadius: 4}}>
				<Img src={staticFile('qr_cave71.svg')} style={{width: 120, height: 120, display: 'block'}} />
			</div>

			{texte && (textes.blocs as Bloc[]).map((b) => <BlocTexte key={b.id} bloc={b} K={K} />)}
		</AbsoluteFill>
	);
};
