/**
 * Phase 3: Product UX & Identity
 *
 * Onboarding Welcome Screen
 * Introduces TORQ Console to first-time users
 */

import { useEffect, useState } from 'react';
import { X, ArrowRight, Sparkles, Zap, Users, Workflow } from 'lucide-react';

interface OnboardingWelcomeProps {
  onComplete: () => void;
  hasSeenBefore?: boolean;
}

export function OnboardingWelcome({ onComplete, hasSeenBefore }: OnboardingWelcomeProps) {
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    {
      icon: Sparkles,
      title: 'Welcome to TORQ Console',
      description: 'Your AI-powered agent orchestration platform',
      content: 'TORQ Console brings together multiple AI agents that can search, code, research, and collaborate to help you build faster.',
    },
    {
      icon: Users,
      title: 'Meet Prince Flowers',
      description: 'Your primary AI agent for complex tasks',
      content: 'Prince Flowers specializes in web research, code generation, and coordinating other specialized agents. Just ask naturally - Prince will route your request to the right expert.',
    },
    {
      icon: Workflow,
      title: 'Automate with Workflows',
      description: 'Build and execute automated agent workflows',
      content: 'Create visual workflows that chain multiple agents together. Schedule recurring tasks, or trigger workflows manually when you need them.',
    },
    {
      icon: Zap,
      title: 'Get Started',
      description: 'You\'re ready to go!',
      content: 'Start by chatting with Prince Flowers, or explore the Workflows tab to see what\'s possible. Everything you need is right here.',
    },
  ];

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handleComplete = () => {
    // Mark as seen in localStorage
    localStorage.setItem('torq-onboarding-seen', 'true');
    onComplete();
  };

  const handleSkip = () => {
    handleComplete();
  };

  const step = steps[currentStep];
  const Icon = step.icon;
  const isLastStep = currentStep === steps.length - 1;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-300">
        {/* Header with skip button */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <div className="flex gap-1">
              {steps.map((_, i) => (
                <div
                  key={i}
                  className={`h-1.5 rounded-full transition-colors ${
                    i === currentStep ? 'bg-blue-600 w-8' : i < currentStep ? 'bg-blue-600' : 'bg-gray-200'
                  }`}
                />
              ))}
            </div>
          </div>
          <button
            onClick={handleSkip}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-8">
          {/* Icon */}
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mb-6">
            <Icon className="w-8 h-8 text-white" />
          </div>

          {/* Title & Description */}
          <h2 className="text-2xl font-bold text-gray-900 mb-2">{step.title}</h2>
          <p className="text-lg text-blue-600 font-medium mb-4">{step.description}</p>

          {/* Content */}
          <p className="text-gray-600 leading-relaxed">{step.content}</p>

          {/* Feature highlights for first step */}
          {currentStep === 0 && (
            <div className="mt-6 grid grid-cols-3 gap-3">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-2xl mb-1">💬</div>
                <div className="text-xs text-gray-600">Chat</div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-2xl mb-1">⚡</div>
                <div className="text-xs text-gray-600">Automate</div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-2xl mb-1">🤖</div>
                <div className="text-xs text-gray-600">Agents</div>
              </div>
            </div>
          )}

          {/* Example prompts for Prince Flowers step */}
          {currentStep === 1 && (
            <div className="mt-6 space-y-2">
              <p className="text-sm font-medium text-gray-700">Try asking:</p>
              {[
                'Search for the latest React best practices',
                'Help me write a Python script for data analysis',
                'What are the key differences between PostgreSQL and MongoDB?',
              ].map((prompt, i) => (
                <div
                  key={i}
                  className="px-3 py-2 bg-gray-50 rounded-lg text-sm text-gray-700 hover:bg-gray-100 transition-colors cursor-text"
                >
                  "{prompt}"
                </div>
              ))}
            </div>
          )}

          {/* Workflow examples */}
          {currentStep === 2 && (
            <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
              <p className="text-sm font-medium text-gray-700 mb-2">Coming Soon:</p>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Daily research briefings</li>
                <li>• Code review workflows</li>
                <li>• Multi-agent report generation</li>
              </ul>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
          <div className="text-sm text-gray-500">
            Step {currentStep + 1} of {steps.length}
          </div>
          <div className="flex items-center gap-3">
            {!isLastStep && (
              <button
                onClick={handleSkip}
                className="text-gray-500 hover:text-gray-700 text-sm font-medium transition-colors"
              >
                Skip tour
              </button>
            )}
            <button
              onClick={handleNext}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              {isLastStep ? 'Get Started' : 'Continue'}
              <ArrowRight className="w-4 h-4 ml-2" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Hook to check if user has seen onboarding
 */
export function useOnboarding() {
  const [hasSeen, setHasSeen] = useState(true);

  useEffect(() => {
    // Check for ?reset=true or ?show-onboarding=true in URL to reset
    const urlParams = new URLSearchParams(window.location.search);
    const shouldReset = urlParams.has('reset') || urlParams.has('show-onboarding');

    if (shouldReset) {
      localStorage.removeItem('torq-onboarding-seen');
      // Clean URL without reloading
      window.history.replaceState({}, '', window.location.pathname);
      setHasSeen(false);
      return;
    }

    const seen = localStorage.getItem('torq-onboarding-seen');
    setHasSeen(!!seen);
  }, []);

  const markSeen = () => {
    localStorage.setItem('torq-onboarding-seen', 'true');
    setHasSeen(true); // Also update React state to trigger re-render
  };

  return {
    hasSeenOnboarding: hasSeen,
    markOnboardingComplete: markSeen,
    markSeen,
  };
}

/**
 * Compact inline welcome banner (for returning users)
 */
export function WelcomeBanner({ onDismiss, onShowTour }: { onDismiss: () => void; onShowTour: () => void }) {
  return (
    <div className="mx-4 mt-4 p-4 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl text-white animate-in fade-in slide-in-from-top-2 duration-500">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-5 h-5" />
            <h3 className="font-semibold">Welcome back to TORQ Console</h3>
          </div>
          <p className="text-sm text-blue-100">
            Continue where you left off, or take a quick tour to see what's new.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onShowTour}
            className="px-3 py-1.5 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium transition-colors"
          >
            Quick Tour
          </button>
          <button
            onClick={onDismiss}
            className="p-1.5 text-white/70 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
