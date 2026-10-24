'use client';

import { ExpertRecommendation } from '@/types';
import { Star, Clock, DollarSign, MapPin, CheckCircle2, ExternalLink } from 'lucide-react';

interface ExpertCardProps {
  recommendation: ExpertRecommendation;
  index: number;
  onSelect: (expertId: number, expertName: string) => void;
  isLoading: boolean;
}

export function ExpertCard({
  recommendation,
  index,
  onSelect,
  isLoading,
}: ExpertCardProps) {
  const { expert, match } = recommendation;
  const matchPercent = Math.round(match.match_score * 100);

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden hover:shadow-md transition-shadow">
      {/* Match Score Banner */}
      <div className="bg-gradient-to-r from-cyan-500 to-blue-600 px-4 py-2 flex items-center justify-between">
        <span className="text-white text-sm font-medium">
          #{index + 1} Match
        </span>
        <div className="flex items-center gap-1">
          <CheckCircle2 size={16} className="text-white" />
          <span className="text-white font-bold">{matchPercent}%</span>
        </div>
      </div>

      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {expert.is_external && expert.profile_url ? (
                <a
                  href={expert.profile_url}
                  target="_blank"
                  rel="noopener noreferrer nofollow"
                  className="hover:text-primary-600 hover:underline"
                >
                  {expert.name}
                </a>
              ) : (
                expert.name
              )}
            </h3>
            <p className="text-sm text-gray-600">{expert.title}</p>
          </div>

          {expert.is_featured && (
            <span className="px-2 py-1 bg-cyan-50 text-cyan-700 text-xs font-medium rounded-lg border border-cyan-200">
              Featured
            </span>
          )}

          {/* Rating (network experts only - external profiles have no rating here) */}
          {!expert.is_external && expert.total_reviews > 0 && (
            <div className="flex items-center gap-1 bg-yellow-50 px-2 py-1 rounded-lg">
              <Star size={16} className="text-yellow-500 fill-yellow-500" />
              <span className="text-sm font-medium text-yellow-700">
                {expert.rating.toFixed(1)}
              </span>
              <span className="text-xs text-yellow-600">
                ({expert.total_reviews})
              </span>
            </div>
          )}
        </div>

        {/* External freelancer notice and profile link */}
        {expert.is_external && expert.profile_url && (
          <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-xs text-amber-800 mb-2">
              External freelancer profile on {expert.profile_platform || 'a freelance platform'}.
              Not affiliated with this project - reach them through their profile.
            </p>
            <a
              href={expert.profile_url}
              target="_blank"
              rel="noopener noreferrer nofollow"
              className="inline-flex items-center gap-1 text-sm font-medium text-amber-900 underline hover:text-amber-700"
            >
              View profile on {expert.profile_platform || 'their platform'}
              <ExternalLink size={14} />
            </a>
          </div>
        )}

        {/* Bio */}
        {expert.bio && (
          <p className="text-sm text-gray-600 mb-4 line-clamp-2">{expert.bio}</p>
        )}

        {/* Info Grid */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          {expert.response_time && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Clock size={16} className="text-gray-400" />
              <span>{expert.response_time}</span>
            </div>
          )}
          {expert.hourly_rate && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <DollarSign size={16} className="text-gray-400" />
              <span>${expert.hourly_rate}/hr</span>
            </div>
          )}
          {expert.location && (
            <div className="flex items-center gap-2 text-sm text-gray-600 col-span-2">
              <MapPin size={16} className="text-gray-400" />
              <span>{expert.location}</span>
            </div>
          )}
        </div>

        {/* Skills */}
        <div className="mb-4">
          <div className="flex flex-wrap gap-2">
            {match.matched_skills.slice(0, 4).map((skill) => (
              <span
                key={skill}
                className="px-2 py-1 bg-green-50 text-green-700 text-xs rounded-full border border-green-200"
              >
                {skill.replace(/_/g, ' ')}
              </span>
            ))}
            {expert.skills.length > 4 && (
              <span className="px-2 py-1 bg-gray-100 text-gray-500 text-xs rounded-full">
                +{expert.skills.length - 4} more
              </span>
            )}
          </div>
        </div>

        {/* Match Reasons */}
        {match.match_reasons.length > 0 && (
          <div className="mb-4 p-3 bg-blue-50 rounded-lg">
            <p className="text-xs text-blue-600 font-medium mb-1">Why this expert:</p>
            <ul className="text-xs text-blue-700 space-y-1">
              {match.match_reasons.slice(0, 2).map((reason, i) => (
                <li key={i} className="flex items-start gap-1">
                  <span className="text-blue-400 mt-0.5">•</span>
                  {reason}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Select Button */}
        <button
          onClick={() => onSelect(expert.id, expert.name)}
          disabled={isLoading}
          className="w-full py-3 px-4 bg-primary-600 text-white font-medium rounded-lg
                     hover:bg-primary-700 transition-colors
                     disabled:bg-gray-300 disabled:cursor-not-allowed
                     focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
        >
          {isLoading
            ? 'Connecting...'
            : expert.is_external
              ? `Choose ${expert.name.split(' ')[0]}`
              : `Connect with ${expert.name.split(' ')[0]}`}
        </button>
      </div>
    </div>
  );
}
