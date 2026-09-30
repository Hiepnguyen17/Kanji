export const DISPLAY_SETTINGS_KEY = 'kanjiai-display-settings-v1';
export const DEFAULT_DISPLAY_SETTINGS = {
  dark_mode: false,
  sound_effects: true,
  kanji_font: 'Noto Serif JP',
};

export const readLocalDisplaySettings = () => {
  try {
    const saved = JSON.parse(localStorage.getItem(DISPLAY_SETTINGS_KEY) || '{}');
    return {
      ...DEFAULT_DISPLAY_SETTINGS,
      ...saved,
      kanji_font: saved.kanji_font || DEFAULT_DISPLAY_SETTINGS.kanji_font,
    };
  } catch {
    return { ...DEFAULT_DISPLAY_SETTINGS };
  }
};

export const writeLocalDisplaySettings = values => {
  try {
    localStorage.setItem(DISPLAY_SETTINGS_KEY, JSON.stringify(values));
  } catch {}
};
