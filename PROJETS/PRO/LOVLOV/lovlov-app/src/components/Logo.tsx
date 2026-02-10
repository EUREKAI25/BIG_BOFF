import { useTranslation } from 'react-i18next';

interface LogoProps {
  className?: string;
}

// Map language codes to logo files
const logoMap: Record<string, string> = {
  fr: '/logo_fr.svg',
  en: '/logo_en.svg',
  es: '/logo_es.svg',
  it: '/logo_it.svg',
  de: '/logo_de.svg',
  pt: '/logo_en.svg', // Fallback to EN for Portuguese (no PT logo yet)
};

export default function Logo({ className = '' }: LogoProps) {
  const { i18n } = useTranslation();

  // Get the base language code (e.g., 'fr' from 'fr-FR')
  const langCode = i18n.language?.split('-')[0] || 'en';
  const logoSrc = logoMap[langCode] || logoMap.en;

  return (
    <img
      src={logoSrc}
      alt="LovLov"
      className={className}
    />
  );
}
