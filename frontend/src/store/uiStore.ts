import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type LanguageCode = 'en' | 'gu' | 'hi';

interface UiState {
  sidebarCollapsed: boolean;
  activeDepartmentId: string | null;
  language: LanguageCode;
  toggleSidebar: () => void;
  setActiveDepartment: (departmentId: string | null) => void;
  setLanguage: (language: LanguageCode) => void;
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      activeDepartmentId: null,
      language: 'en',
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setActiveDepartment: (departmentId) => set({ activeDepartmentId: departmentId }),
      setLanguage: (language) => set({ language }),
    }),
    { name: 'kanadshield-ui' },
  ),
);
