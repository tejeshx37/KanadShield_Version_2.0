import type { LanguageCode } from '../store/uiStore';

// UI chrome translation only. Document body content translation is a
// separate concern served by the backend's document_translation table
// (see docs/API_CONTRACT.md) and is never conflated with this dictionary.
const dictionaries: Record<LanguageCode, Record<string, string>> = {
  en: {
    nav_dashboard: 'Dashboard',
    nav_research: 'Research',
    nav_archives: 'Archives',
    nav_public_service: 'Public Service',
    nav_insights: 'Insights',
    nav_support: 'Support',
    nav_library: 'Library',
    new_research: '+ New Research',
    search_placeholder: 'Search acts, judgments, notifications...',
  },
  hi: {
    nav_dashboard: 'डैशबोर्ड',
    nav_research: 'शोध',
    nav_archives: 'अभिलेख',
    nav_public_service: 'लोक सेवा',
    nav_insights: 'अंतर्दृष्टि',
    nav_support: 'सहायता',
    nav_library: 'पुस्तकालय',
    new_research: '+ नया शोध',
    search_placeholder: 'अधिनियम, निर्णय, अधिसूचनाएँ खोजें...',
  },
  gu: {
    nav_dashboard: 'ડેશબોર્ડ',
    nav_research: 'સંશોધન',
    nav_archives: 'આર્કાઇવ્સ',
    nav_public_service: 'જાહેર સેવા',
    nav_insights: 'આંતરદૃષ્ટિ',
    nav_support: 'સહાય',
    nav_library: 'પુસ્તકાલય',
    new_research: '+ નવું સંશોધન',
    search_placeholder: 'અધિનિયમ, ચુકાદા, સૂચનાઓ શોધો...',
  },
};

export function t(key: string, language: LanguageCode): string {
  return dictionaries[language][key] ?? dictionaries.en[key] ?? key;
}

export const languageLabels: Record<LanguageCode, string> = {
  en: 'English',
  gu: 'ગુજરાતી',
  hi: 'हिं',
};
