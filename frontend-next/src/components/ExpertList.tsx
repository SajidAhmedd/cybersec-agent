'use client';

import { ExpertRecommendation } from '@/types';
import { ExpertCard } from './ExpertCard';
import { Users } from 'lucide-react';

interface ExpertListProps {
  experts: ExpertRecommendation[];
  onSelect: (expertId: number, expertName: string) => void;
  isLoading: boolean;
}

export function ExpertList({ experts, onSelect, isLoading }: ExpertListProps) {
  if (!experts || experts.length === 0) {
    return null;
  }

  return (
    <div className="py-6 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
            <Users size={20} className="text-white" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Recommended Experts
            </h2>
            <p className="text-sm text-gray-500">
              {experts.length} expert{experts.length !== 1 ? 's' : ''} matched to your situation
            </p>
          </div>
        </div>

        {/* Expert Cards Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {experts.map((recommendation, index) => (
            <ExpertCard
              key={recommendation.expert.id}
              recommendation={recommendation}
              index={index}
              onSelect={onSelect}
              isLoading={isLoading}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
