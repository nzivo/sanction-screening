import React, { useEffect, useState } from "react";
import {
  AlertCircle,
  CheckCircle,
  Database,
  TrendingUp,
  RefreshCw,
  Clock,
  Calendar,
} from "lucide-react";
import {
  sanctionsAPI,
  pepAPI,
  worldBankAPI,
  frcKenyaAPI,
} from "../services/api";

function StatCard({ title, value, icon: Icon, color = "blue", loading }) {
  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-600 text-sm font-medium">{title}</p>
          <p className={`text-3xl font-bold text-${color}-600 mt-2`}>
            {loading ? "..." : value?.toLocaleString() || "0"}
          </p>
        </div>
        <div className={`p-4 bg-${color}-100 rounded-full`}>
          <Icon className={`text-${color}-600`} size={32} />
        </div>
      </div>
    </div>
  );
}

function ListStatusCard({ list, onUpdate }) {
  const [updating, setUpdating] = useState(false);

  const handleUpdate = async () => {
    setUpdating(true);
    try {
      await sanctionsAPI.updateList(list.source, true);
      onUpdate();
    } catch (error) {
      console.error("Update failed:", error);
    }
    setUpdating(false);
  };

  const getStatusColor = () => {
    if (list.needs_update) return "yellow";
    return "green";
  };

  const statusColor = getStatusColor();

  return (
    <div className="bg-white rounded-lg p-4 border border-gray-200 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-1">
            <h3 className="font-semibold text-lg">{list.source}</h3>
            <div className={`w-2 h-2 rounded-full bg-${statusColor}-500`}></div>
          </div>
          <p className="text-sm text-gray-600">
            {list.count?.toLocaleString() || 0} entities
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Last updated:{" "}
            {list.last_update
              ? new Date(list.last_update).toLocaleDateString()
              : "Never"}
          </p>
          {list.needs_update && (
            <p className="text-xs text-yellow-600 mt-1 font-medium">
              ⚠️ Update recommended
            </p>
          )}
        </div>
        <button
          onClick={handleUpdate}
          disabled={updating}
          className="btn-primary flex items-center space-x-2 disabled:opacity-50 text-sm"
        >
          <RefreshCw size={14} className={updating ? "animate-spin" : ""} />
          <span>{updating ? "Updating..." : "Update"}</span>
        </button>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState({
    loading: true,
    lists: [],
    schedule: [],
    pepCount: 0,
    worldBankCount: 0,
    frcKenyaCount: 0,
    totalEntities: 0,
  });

  const loadStats = async () => {
    try {
      const [
        listsResponse,
        scheduleResponse,
        pepResponse,
        wbResponse,
        frcResponse,
      ] = await Promise.all([
        sanctionsAPI.checkUpdates(),
        sanctionsAPI.getSchedule(),
        pepAPI.getPEPStats().catch(() => ({ data: { count: 0 } })),
        worldBankAPI.getStats().catch(() => ({ data: { count: 0 } })),
        frcKenyaAPI.getStats().catch(() => ({ data: { count: 0 } })),
      ]);

      // Transform sources object to lists array
      const sourcesData = listsResponse.data.sources || {};
      const lists = Object.keys(sourcesData).map((source) => ({
        source,
        count: sourcesData[source].entity_count || 0,
        last_update: sourcesData[source].last_update,
        needs_update: sourcesData[source].should_update || false,
      }));

      // Transform schedule object to schedule array
      const scheduleData = scheduleResponse.data.schedule || {};
      const schedule = Object.keys(scheduleData).map((source) => ({
        source,
        interval_hours: scheduleData[source].update_interval_hours || null,
        auto_update:
          scheduleData[source].should_update !== undefined
            ? !scheduleData[source].reason?.includes("Manual")
            : true,
        description: scheduleData[source].reason || "",
      }));

      const totalSanctions = lists.reduce(
        (sum, list) => sum + (list.count || 0),
        0,
      );
      const totalEntities =
        totalSanctions +
        (pepResponse.data.count || 0) +
        (wbResponse.data.count || 0) +
        (frcResponse.data.count || 0);

      setStats({
        loading: false,
        lists,
        schedule,
        pepCount: pepResponse.data.count || 0,
        worldBankCount: wbResponse.data.count || 0,
        frcKenyaCount: frcResponse.data.count || 0,
        totalEntities,
      });
    } catch (error) {
      console.error("Failed to load stats:", error);
      setStats((prev) => ({ ...prev, loading: false }));
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <button
          onClick={loadStats}
          className="btn-secondary flex items-center space-x-2"
        >
          <RefreshCw size={18} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Entities"
          value={stats.totalEntities}
          icon={Database}
          color="blue"
          loading={stats.loading}
        />
        <StatCard
          title="Sanctions Lists"
          value={stats.lists.reduce((sum, l) => sum + (l.count || 0), 0)}
          icon={AlertCircle}
          color="red"
          loading={stats.loading}
        />
        <StatCard
          title="PEP Records"
          value={stats.pepCount}
          icon={CheckCircle}
          color="green"
          loading={stats.loading}
        />
        <StatCard
          title="World Bank"
          value={stats.worldBankCount}
          icon={TrendingUp}
          color="purple"
          loading={stats.loading}
        />
      </div>

      {/* Lists Status */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Sanctions Lists Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {stats.lists.map((list) => (
            <ListStatusCard
              key={list.source}
              list={list}
              onUpdate={loadStats}
            />
          ))}
        </div>
      </div>

      {/* Additional Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-xl font-bold mb-4">Quick Stats</h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center py-2 border-b">
              <span className="text-gray-600">FRC Kenya</span>
              <span className="font-semibold">
                {stats.frcKenyaCount.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span className="text-gray-600">World Bank Debarred</span>
              <span className="font-semibold">
                {stats.worldBankCount.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-gray-600">Politically Exposed Persons</span>
              <span className="font-semibold">
                {stats.pepCount.toLocaleString()}
              </span>
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="text-xl font-bold mb-4">System Status</h2>
          <div className="space-y-3">
            {/* Update Schedule */}
            {stats.schedule.length > 0 && (
              <div className="card">
                <div className="flex items-center space-x-2 mb-4">
                  <Calendar className="text-primary-600" size={24} />
                  <h2 className="text-xl font-bold">Update Schedule</h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                          Source
                        </th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                          <div className="flex items-center space-x-1">
                            <Clock size={16} />
                            <span>Interval</span>
                          </div>
                        </th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                          Auto Update
                        </th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                          Description
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {stats.schedule.map((item) => (
                        <tr key={item.source} className="hover:bg-gray-50">
                          <td className="px-4 py-3 font-medium">
                            {item.source}
                          </td>
                          <td className="px-4 py-3 text-gray-600">
                            {item.interval_hours} hours
                            {item.interval_hours === 24 && " (Daily)"}
                            {item.interval_hours === 168 && " (Weekly)"}
                          </td>
                          <td className="px-4 py-3">
                            <span
                              className={`px-2 py-1 rounded text-xs font-semibold ${
                                item.auto_update
                                  ? "bg-green-100 text-green-800"
                                  : "bg-gray-100 text-gray-800"
                              }`}
                            >
                              {item.auto_update ? "Yes" : "Manual"}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {item.description}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
            <div className="flex items-center space-x-3 py-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-gray-700">API Status: Online</span>
            </div>
            <div className="flex items-center space-x-3 py-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-gray-700">Database: Connected</span>
            </div>
            <div className="flex items-center space-x-3 py-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
              <span className="text-gray-700">Updates: Automated</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
