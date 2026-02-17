import React, { useState } from 'react';
import { useAgentStore } from '@/stores/agentStore';
import type { Agent } from '@/lib/types';

interface AddAgentModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const AGENT_TYPES = [
    { value: 'orchestrator', label: '🌸 Orchestrator', description: 'Routes queries to other agents' },
    { value: 'code', label: '💻 Code', description: 'Generates and edits code' },
    { value: 'debug', label: '🐛 Debug', description: 'Analyzes and fixes errors' },
    { value: 'docs', label: '📚 Documentation', description: 'Writes docs and guides' },
    { value: 'test', label: '🧪 Testing', description: 'Creates and runs tests' },
    { value: 'architecture', label: '🏗️ Architecture', description: 'System design and patterns' },
    { value: 'research', label: '🔍 Research', description: 'Web search and analysis' },
];

export const AddAgentModal: React.FC<AddAgentModalProps> = ({ isOpen, onClose }) => {
    const { agents, setAgents } = useAgentStore();
    const [name, setName] = useState('');
    const [type, setType] = useState('code');
    const [capabilities, setCapabilities] = useState('');

    if (!isOpen) return null;

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!name.trim()) return;

        const newAgent: Agent = {
            id: `agent_${Date.now()}`,
            name: name.trim(),
            status: 'idle',
            type,
            capabilities: capabilities.split(',').map((c) => c.trim()).filter(Boolean),
        };

        setAgents([...agents, newAgent]);
        setName('');
        setType('code');
        setCapabilities('');
        onClose();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
            <div className="bg-bg-secondary border border-border rounded-xl w-[480px] shadow-2xl" onClick={(e) => e.stopPropagation()}>
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                    <h2 className="text-h3 font-semibold">Add New Agent</h2>
                    <button onClick={onClose} className="text-text-muted hover:text-text-primary transition-colors text-xl leading-none">
                        ×
                    </button>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="p-6 space-y-5">
                    {/* Name */}
                    <div>
                        <label className="block text-small text-text-secondary mb-1.5">Agent Name</label>
                        <input
                            autoFocus
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="e.g. Data Analyst"
                            className="w-full bg-bg-tertiary text-text-primary rounded-lg px-3 py-2.5 text-body border border-border focus:outline-none focus:ring-2 focus:ring-accent-primary/50 focus:border-accent-primary"
                        />
                    </div>

                    {/* Type */}
                    <div>
                        <label className="block text-small text-text-secondary mb-1.5">Agent Type</label>
                        <div className="grid grid-cols-2 gap-2">
                            {AGENT_TYPES.map((t) => (
                                <button
                                    key={t.value}
                                    type="button"
                                    onClick={() => setType(t.value)}
                                    className={`text-left px-3 py-2 rounded-lg border text-small transition-all ${type === t.value
                                            ? 'border-accent-primary bg-accent-primary/10 text-accent-primary'
                                            : 'border-border hover:border-border-focus text-text-secondary'
                                        }`}
                                >
                                    <div className="font-medium">{t.label}</div>
                                    <div className="text-text-muted text-xs mt-0.5">{t.description}</div>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Capabilities */}
                    <div>
                        <label className="block text-small text-text-secondary mb-1.5">Capabilities (comma-separated)</label>
                        <input
                            type="text"
                            value={capabilities}
                            onChange={(e) => setCapabilities(e.target.value)}
                            placeholder="e.g. SQL, Data Viz, Analytics"
                            className="w-full bg-bg-tertiary text-text-primary rounded-lg px-3 py-2.5 text-body border border-border focus:outline-none focus:ring-2 focus:ring-accent-primary/50 focus:border-accent-primary"
                        />
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
                            type="submit"
                            disabled={!name.trim()}
                            className="flex-1 px-4 py-2.5 rounded-lg bg-accent-primary text-white font-medium hover:brightness-110 transition-all disabled:opacity-40 disabled:cursor-not-allowed text-small"
                        >
                            Add Agent
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
