%##########################################################################
%
%   ConceptionFiltre.m :
%
%   Fichier de calcul des coefficients du filtre
%
%   Entr�es :
%
%   Sortie :  %       - NumCas (4*3) : Num�rateurs des filtres cascad�s
%       - DenCas (4*3) : D�nominateurs des filtres cascad�s
%       - Num (1*9) : Num�rateur du filtre non-cascad�
%       - Den (1*9) : D�nominateur du filtre non-cascad�
%
%   Fonction :
%       - Calcul des coefficients du filtre
%       - Calcul des coefficients du filtre cascad�
%
%##########################################################################

   Fe = 12000;                  % Frequence d'echantillonnage

   % Sp�cification du filtre 
     Fp1 = 1200;                 % Fr�quence basse de la bande passante
   Fp2 = 2400;                 % Fr�quence haute de la bande passante
   Fs1 = 1080;                 % Fr�quence basse de la bande att�nu�e
   Fs2 = 2520;                 % Fr�quence haute de la bande att�nu�e
      Wp = [2*Fp1/Fe 2*Fp2/Fe];   % Fr�quences hautes et basses de la bande passante
   Ws = [2*Fs1/Fe 2*Fs2/Fe];   % Fr�quences hautes et basses de la bande att�nu�e
   Rp = 3;                     % Att�nuation dans la bande passante
   Rs = 30;                    % Att�nuation dans la bande att�nu�e
        % Calcul de l'ordre du filtre
     [Nf, Wn] = buttord(Wp, Ws, Rp, Rs);      % Butterworth
    disp(strcat(sprintf('\n Ordre du filtre - Butterworth : '), num2str(2 * Nf) ));

   [Nf, Wn] = Cheb1ord(Wp, Ws, Rp, Rs);     % Chebyshev type I
    disp(strcat(sprintf('\n Ordre du filtre - Chebyshev type I : '), num2str(2 * Nf) ));       
	[Nf, Wn] = Cheb2ord(Wp, Ws, Rp, Rs);    % Chebyshev type II
    disp(strcat(sprintf('\n Ordre du filtre - Chebyshev type II : '), num2str(2 * Nf) ));       
	[Nf, Wn] = ellipord(Wp, Ws, Rp, Rs);    % Elliptique
    disp(strcat(sprintf('\n Ordre du filtre - Elliptique : '), num2str(2 * Nf) ));  
      % Calcul des coefficients du filtre - choisir le filtre d'ordre
   % minimal      
   [Num,Den] = ellip(Nf, Rp, Rs, Wn);
     % Calcul des coefficients du filtre cascad�
   