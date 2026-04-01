import React, { useState } from "react";
import { Search, AlertTriangle, CheckCircle, Info } from "lucide-react";
import { screeningAPI } from "../services/api";

function MatchCard({ match }) {
  const getSeverityColor = (score) => {
    if (score >= 90) return "red";
    if (score >= 80) return "yellow";
    return "blue";
  };

  const color = getSeverityColor(match.match_score);

  return (
    <div
      className={`border-l-4 border-${color}-500 bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <h3 className="font-bold text-lg">{match.full_name}</h3>
            <span
              className={`px-2 py-1 rounded text-xs font-semibold bg-${color}-100 text-${color}-800`}
            >
              {match.match_score}% Match
            </span>
          </div>

          <div className="mt-2 space-y-1 text-sm">
            <p className="text-gray-600">
              <span className="font-medium">Source:</span> {match.source} -{" "}
              {match.list_type}
            </p>
            {match.entity_type && (
              <p className="text-gray-600">
                <span className="font-medium">Type:</span> {match.entity_type}
              </p>
            )}
            {match.date_of_birth && (
              <p className="text-gray-600">
                <span className="font-medium">DOB:</span> {match.date_of_birth}
              </p>
            )}
            {match.nationality && (
              <p className="text-gray-600">
                <span className="font-medium">Nationality:</span>{" "}
                {match.nationality}
              </p>
            )}
            {match.aliases && match.aliases.length > 0 && (
              <div className="text-gray-600">
                <span className="font-medium">Aliases:</span>
                <div className="ml-4 mt-1">
                  {match.aliases.map((alias, idx) => (
                    <span
                      key={idx}
                      className="inline-block bg-gray-100 rounded px-2 py-1 text-xs mr-2 mb-1"
                    >
                      {alias.name}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {match.remarks && (
              <p className="text-gray-600 text-xs mt-2 border-t pt-2">
                <span className="font-medium">Remarks:</span> {match.remarks}
              </p>
            )}
          </div>
        </div>

        <div className="ml-4">
          {match.match_score >= 90 ? (
            <AlertTriangle className="text-red-500" size={24} />
          ) : match.match_score >= 80 ? (
            <AlertTriangle className="text-yellow-500" size={24} />
          ) : (
            <Info className="text-blue-500" size={24} />
          )}
        </div>
      </div>
    </div>
  );
}

export default function Screening() {
  const [formData, setFormData] = useState({
    name: "",
    date_of_birth: "",
    country: "",
    entity_type: "individual",
  });

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setError("Please enter a name to screen");
      return;
    }

    setLoading(true);
    setError("");
    setResults(null);

    try {
      const response = await screeningAPI.screenName(formData);
      setResults(response.data);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Screening failed. Please try again.",
      );
      console.error("Screening error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFormData({
      name: "",
      date_of_birth: "",
      country: "",
      entity_type: "individual",
    });
    setResults(null);
    setError("");
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Sanctions Screening</h1>

      {/* Screening Form */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Screen Individual or Entity</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Full Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                className="input-field"
                placeholder="Enter name to screen"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Entity Type
              </label>
              <select
                value={formData.entity_type}
                onChange={(e) =>
                  setFormData({ ...formData, entity_type: e.target.value })
                }
                className="input-field"
              >
                <option value="individual">Individual</option>
                <option value="entity">Entity</option>
                <option value="vessel">Vessel</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Date of Birth (Optional)
              </label>
              <input
                type="date"
                value={formData.date_of_birth}
                onChange={(e) =>
                  setFormData({ ...formData, date_of_birth: e.target.value })
                }
                className="input-field"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Country (Optional)
              </label>
              <input
                type="text"
                value={formData.country}
                onChange={(e) =>
                  setFormData({ ...formData, country: e.target.value })
                }
                className="input-field"
                placeholder="e.g., Kenya, USA"
              />
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center space-x-2">
              <AlertTriangle className="text-red-500" size={20} />
              <p className="text-red-700">{error}</p>
            </div>
          )}

          <div className="flex space-x-3">
            <button
              type="submit"
              disabled={loading}
              className="btn-primary flex items-center space-x-2 disabled:opacity-50"
            >
              <Search size={18} />
              <span>{loading ? "Screening..." : "Screen Now"}</span>
            </button>
            <button
              type="button"
              onClick={handleReset}
              className="btn-secondary"
            >
              Reset
            </button>
          </div>
        </form>
      </div>

      {/* Results */}
      {results && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">Screening Results</h2>
            {results.total_matches > 0 ? (
              <span className="px-4 py-2 bg-red-100 text-red-800 rounded-lg font-semibold flex items-center space-x-2">
                <AlertTriangle size={20} />
                <span>MATCH FOUND</span>
              </span>
            ) : (
              <span className="px-4 py-2 bg-green-100 text-green-800 rounded-lg font-semibold flex items-center space-x-2">
                <CheckCircle size={20} />
                <span>NO MATCH</span>
              </span>
            )}
          </div>

          <div className="mb-4 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">
              <span className="font-medium">Screened Name:</span>{" "}
              {results.query_name}
            </p>
            <p className="text-sm text-gray-600">
              <span className="font-medium">Total Matches:</span>{" "}
              {results.total_matches}
            </p>
            <p className="text-sm text-gray-600">
              <span className="font-medium">Highest Score:</span>{" "}
              {results.highest_score}%
            </p>
            <p className="text-sm text-gray-600">
              <span className="font-medium">Threshold Used:</span>{" "}
              {results.threshold_used}%
            </p>
            {results.near_misses && results.near_misses.length > 0 && (
              <p className="text-sm text-gray-600">
                <span className="font-medium">Near Misses:</span>{" "}
                {results.near_misses.length} (scores{" "}
                {results.threshold_used - 10}-{results.threshold_used - 1}%)
              </p>
            )}
          </div>

          {(results.sanctions_matches &&
            results.sanctions_matches.length > 0) ||
          (results.pep_matches && results.pep_matches.length > 0) ? (
            <div className="space-y-4">
              {results.sanctions_matches &&
                results.sanctions_matches.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="font-semibold text-lg text-red-700">
                      Sanctions Matches ({results.sanctions_matches.length})
                    </h3>
                    {results.sanctions_matches.map((match, idx) => (
                      <MatchCard key={`sanction-${idx}`} match={match} />
                    ))}
                  </div>
                )}

              {results.pep_matches && results.pep_matches.length > 0 && (
                <div className="space-y-3">
                  <h3 className="font-semibold text-lg text-orange-700">
                    PEP Matches ({results.pep_matches.length})
                  </h3>
                  {results.pep_matches.map((match, idx) => (
                    <MatchCard key={`pep-${idx}`} match={match} />
                  ))}
                </div>
              )}

              {/* Near Misses Section */}
              {results.near_misses && results.near_misses.length > 0 && (
                <div className="space-y-3 mt-6 pt-6 border-t border-gray-200">
                  <div className="flex items-center space-x-2">
                    <Info className="text-blue-500" size={20} />
                    <h3 className="font-semibold text-lg text-blue-700">
                      Near Misses ({results.near_misses.length})
                    </h3>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">
                    These entries scored {results.threshold_used - 10}% to{" "}
                    {results.threshold_used - 1}% - close to the threshold but
                    not exact matches. Review for potential matches.
                  </p>
                  {results.near_misses.map((match, idx) => (
                    <MatchCard key={`near-miss-${idx}`} match={match} />
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-6">
              <div className="text-center py-8 text-gray-500">
                <CheckCircle
                  size={48}
                  className="mx-auto mb-2 text-green-500"
                />
                <p className="text-lg">
                  No matches found in sanctions databases
                </p>
                <p className="text-sm mt-2">
                  No entries scored above {results.threshold_used}% match
                  threshold
                </p>
              </div>

              {/* Show Near Misses even when no exact matches */}
              {results.near_misses && results.near_misses.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <Info className="text-blue-500" size={20} />
                    <h3 className="font-semibold text-lg text-blue-700">
                      Near Misses ({results.near_misses.length})
                    </h3>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">
                    These entries scored {results.threshold_used - 10}% to{" "}
                    {results.threshold_used - 1}% - close to the threshold.
                    While not exact matches, you may want to review them
                    manually.
                  </p>
                  {results.near_misses.map((match, idx) => (
                    <MatchCard key={`near-miss-${idx}`} match={match} />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
