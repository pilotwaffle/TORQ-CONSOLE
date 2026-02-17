import React, { useState, useEffect } from 'react';

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
}

interface Settings {
    backendUrl: string;
    apiKey: string;
    theme: 'dark' | 'light' | 'auto';
    enableNotifications: boolean;
    autoReconnect: boolean;
}

const DEFAULT_SETTINGS: Settings = {
    backendUrl: 'http://localhost:8899',
    apiKey: '',
    theme: 'dark',
    enableNotifications: true,
    autoReconnect: true,
};

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
    const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);
    const [saved, setSaved] = useState(false);

    useEffect(() => {
        if (isOpen) {
            const stored = localStorage.getItem('torq_settings');
            if (stored) {
                try {
                    setSettings({ ...DEFAULT_SETTINGS, ...JSON.parse(stored) });
                } catch {
                    setSettings(DEFAULT_SETTINGS);
                }
            }
            setSaved(false);
        }
    }, [isOpen]);

    if (!isOpen) return null;

    const handleSave = () => {
        localStorage.setItem('torq_settings', JSON.stringify(settings));
        setSaved(true);
        setTimeout(() => onClose(), 800);
    };

    const updateSetting = <K extends keyof Settings>(key: K, value: Settings[K]) => {
        setSettings((prev) => ({ ...prev, [key]: value }));
        setSaved(false);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
            <div className="bg-bg-secondary border border-border rounded-xl w-[520px] shadow-2xl" onClick={(e) => e.stopPropagation()}>
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                    <h2 className="text-h3 font-semibold">⚙️ Settings</h2>
                    <button onClick={onClose} className="text-text-muted hover:text-text-primary transition-colors text-xl leading-none">
                        ×
                    </button>
                </div>

                {/* Settings */}
                <div className="p-6 space-y-5">
                    {/* Backend URL */}
                    <div>
                        <label className="block text-small text-text-secondary mb-1.5">Backend URL</label>
                        <input
                            type="text"
                            value={settings.backendUrl}
                            onChange={(e) => updateSetting('backendUrl', e.target.value)}
                            className="w-full bg-bg-tertiary text-text-primary rounded-lg px-3 py-2.5 text-body border border-border focus:outline-none focus:ring-2 focus:ring-accent-primary/50 focus:border-accent-primary"
                        />
                        <p className="text-xs text-text-muted mt-1">The TORQ Console backend server address</p>
                    </div>

                    {/* API Key */}
                    <div>
                        <label className="block text-small text-text-secondary mb-1.5">API Key</label>
                        <input
                            type="password"
                            value={settings.apiKey}
                            onChange={(e) => updateSetting('apiKey', e.target.value)}
                            placeholder="Enter your API key..."
                            className="w-full bg-bg-tertiary text-text-primary rounded-lg px-3 py-2.5 text-body border border-border focus:outline-none focus:ring-2 focus:ring-accent-primary/50 focus:border-accent-primary"
                        />
                    </div>

                    {/* Theme */}
                    <div>
                        <label className="block text-small text-text-secondary mb-1.5">Theme</label>
                        <div className="flex gap-2">
                            {(['dark', 'light', 'auto'] as const).map((t) => (
                                <button
                                    key={t}
                                    onClick={() => updateSetting('theme', t)}
                                    className={`flex-1 px-3 py-2 rounded-lg border text-small capitalize transition-all ${settings.theme === t
                                            ? 'border-accent-primary bg-accent-primary/10 text-accent-primary font-medium'
                                            : 'border-border hover:border-border-focus text-text-secondary'
                                        }`}
                                >
                                    {t === 'dark' ? '🌙 ' : t === 'light' ? '☀️ ' : '🔄 '}{t}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Toggles */}
                    <div className="space-y-3">
                        <label className="flex items-center justify-between cursor-pointer group">
                            <span className="text-small text-text-secondary group-hover:text-text-primary transition-colors">
                                Enable Notifications
                            </span>
                            <div
                                onClick={() => updateSetting('enableNotifications', !settings.enableNotifications)}
                                className={`w-10 h-5 rounded-full transition-colors relative cursor-pointer ${settings.enableNotifications ? 'bg-accent-primary' : 'bg-bg-tertiary border border-border'
                                    }`}
                            >
                                <div className={`w-4 h-4 rounded-full bg-white absolute top-0.5 transition-transform ${settings.enableNotifications ? 'translate-x-5' : 'translate-x-0.5'
                                    }`} />
                            </div>
                        </label>

                        <label className="flex items-center justify-between cursor-pointer group">
                            <span className="text-small text-text-secondary group-hover:text-text-primary transition-colors">
                                Auto Reconnect
                            </span>
                            <div
                                onClick={() => updateSetting('autoReconnect', !settings.autoReconnect)}
                                className={`w-10 h-5 rounded-full transition-colors relative cursor-pointer ${settings.autoReconnect ? 'bg-accent-primary' : 'bg-bg-tertiary border border-border'
                                    }`}
                            >
                                <div className={`w-4 h-4 rounded-full bg-white absolute top-0.5 transition-transform ${settings.autoReconnect ? 'translate-x-5' : 'translate-x-0.5'
                                    }`} />
                            </div>
                        </label>
                    </div>

                    {/* Buttons */}
                    <div className="flex gap-3 pt-2">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 px-4 py-2.5 rounded-lg border border-border text-text-secondary hover:bg-bg-tertiary transition-colors text-small"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleSave}
                            className={`flex-1 px-4 py-2.5 rounded-lg font-medium transition-all text-small ${saved
                                    ? 'bg-green-600 text-white'
                                    : 'bg-accent-primary text-white hover:brightness-110'
                                }`}
                        >
                            {saved ? '✓ Saved!' : 'Save Settings'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
