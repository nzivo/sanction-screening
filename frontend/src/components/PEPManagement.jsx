import React, { useState } from "react";
import { Upload, Search, Users, AlertCircle } from "lucide-react";
import { pepAPI } from "../services/api";

export default function PEPManagement() {
  const [activeTab, setActiveTab] = useState("upload");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [stats, setStats] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setUploadResult(null);
  };

  const handleUpload = async () => {
    if (!file) {
      alert("Please select a file");
      return;
    }

    setUploading(true);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await pepAPI.uploadPEP(formData);
      setUploadResult(response.data);
      setFile(null);

      // Reload stats
      loadStats();
    } catch (error) {
      console.error("Upload failed:", error);
      alert(
        "Upload failed: " + (error.response?.data?.detail || error.message),
      );
    } finally {
      setUploading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      alert("Please enter a search query");
      return;
    }

    setSearching(true);
    try {
      const response = await pepAPI.searchPEP({ name: searchQuery, limit: 50 });
      setSearchResults(response.data || []);
    } catch (error) {
      console.error("Search failed:", error);
      alert(
        "Search failed: " + (error.response?.data?.detail || error.message),
      );
    } finally {
      setSearching(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await pepAPI.getPEPStats();
      setStats(response.data);
    } catch (error) {
      console.error("Failed to load stats:", error);
    }
  };

  React.useEffect(() => {
    loadStats();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">PEP Management</h1>
        {stats && (
          <div className="flex items-center space-x-2 bg-primary-100 px-4 py-2 rounded-lg">
            <Users className="text-primary-600" size={20} />
            <span className="font-semibold text-primary-800">
              {stats.count?.toLocaleString() || 0} PEP Records
            </span>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab("upload")}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === "upload"
                ? "border-primary-600 text-primary-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            <Upload size={18} className="inline mr-2" />
            Upload PEP List
          </button>
          <button
            onClick={() => setActiveTab("search")}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
              activeTab === "search"
                ? "border-primary-600 text-primary-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            <Search size={18} className="inline mr-2" />
            Search PEP
          </button>
        </nav>
      </div>

      {/* Upload Tab */}
      {activeTab === "upload" && (
        <div className="card">
          <h2 className="text-xl font-bold mb-4">Upload PEP List</h2>
          <p className="text-gray-600 mb-4">
            Upload an Excel or CSV file containing PEP (Politically Exposed
            Persons) data.
          </p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select File (Excel or CSV)
              </label>
              <input
                type="file"
                accept=".xlsx,.xls,.csv"
                onChange={handleFileChange}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
              />
            </div>

            <button
              onClick={handleUpload}
              disabled={!file || uploading}
              className="btn-primary disabled:opacity-50 flex items-center space-x-2"
            >
              <Upload size={18} />
              <span>{uploading ? "Uploading..." : "Upload"}</span>
            </button>

            {uploadResult && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h3 className="font-semibold text-green-800 mb-2">
                  Upload Successful!
                </h3>
                <div className="text-sm text-green-700 space-y-1">
                  <p>• Added: {uploadResult.added}</p>
                  <p>• Updated: {uploadResult.updated}</p>
                  {uploadResult.errors > 0 && (
                    <p>• Errors: {uploadResult.errors}</p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Search Tab */}
      {activeTab === "search" && (
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-xl font-bold mb-4">Search PEP Records</h2>

            <div className="flex space-x-3">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSearch()}
                placeholder="Enter name to search..."
                className="input-field flex-1"
              />
              <button
                onClick={handleSearch}
                disabled={searching}
                className="btn-primary disabled:opacity-50 flex items-center space-x-2"
              >
                <Search size={18} />
                <span>{searching ? "Searching..." : "Search"}</span>
              </button>
            </div>
          </div>

          {searchResults.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-bold mb-4">
                Results ({searchResults.length})
              </h3>
              <div className="space-y-3">
                {searchResults.map((pep) => (
                  <div
                    key={pep.id}
                    className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-bold text-lg">{pep.full_name}</h4>
                        <div className="mt-2 space-y-1 text-sm text-gray-600">
                          {pep.position && (
                            <p>
                              <span className="font-medium">Position:</span>{" "}
                              {pep.position}
                            </p>
                          )}
                          {pep.country && (
                            <p>
                              <span className="font-medium">Country:</span>{" "}
                              {pep.country}
                            </p>
                          )}
                          {pep.category && (
                            <p>
                              <span className="font-medium">Category:</span>{" "}
                              {pep.category}
                            </p>
                          )}
                          {pep.date_of_birth && (
                            <p>
                              <span className="font-medium">DOB:</span>{" "}
                              {pep.date_of_birth}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
