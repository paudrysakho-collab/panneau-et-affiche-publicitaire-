import React from 'react';
import {Still} from 'remotion';
import {Panneau, LARGEUR, HAUTEUR} from './Panneau';

// A1 portrait (594 x 841 mm). Export x2.829 = 3508 x 4962 px, 150 dpi.
export const RemotionRoot: React.FC = () => (
	<>
		{/* Version sombre (lie-de-vin) */}
		<Still id="Panneau" component={Panneau} width={LARGEUR} height={HAUTEUR} defaultProps={{texte: true, clair: false}} />
		{/* Version claire (blanc chaud) */}
		<Still id="PanneauClair" component={Panneau} width={LARGEUR} height={HAUTEUR} defaultProps={{texte: true, clair: true}} />
		{/* Modèles à partir des vrais produits détourés, un par un (sans IA) */}
		<Still id="PanneauModele1" component={Panneau} width={LARGEUR} height={HAUTEUR} defaultProps={{texte: true, clair: false, photo: 'rangee'}} />
		<Still id="PanneauModele2" component={Panneau} width={LARGEUR} height={HAUTEUR} defaultProps={{texte: true, clair: false, photo: 'gradins'}} />
		{/* Fonds sans texte ni logo, pour les PPTX modifiables */}
		<Still id="PanneauFond" component={Panneau} width={LARGEUR} height={HAUTEUR} defaultProps={{texte: false, clair: false}} />
		<Still id="PanneauClairFond" component={Panneau} width={LARGEUR} height={HAUTEUR} defaultProps={{texte: false, clair: true}} />
	</>
);
