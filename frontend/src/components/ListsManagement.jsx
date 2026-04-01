import React, { useEffect, useState } from "react";
import { RefreshCw, Download, Calendar, AlertCircle } from "lucide-react";
import { sanctionsAPI } from "../services/api";

export default function ListsManagement() {
  const [lists, setLists] = useState([]);
  const [schedule, setSchedule] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState({});

  const loadData = async () => {
    try {
      const [listsRes, scheduleRes] = await Promise.all([
        sanctionsAPI.checkUpdates(),
        sanctionsAPI.getSchedule(),
      ]);

      // Transform sources object to lists array
      const sourcesData = listsRes.data.sources || {};
      const listsArray = Object.keys(sourcesData).map((source) => ({
        source,
        count: sourcesData[source].entity_count || 0,
        last_update: sourcesData[source].last_update,
        needs_update: sourcesData[source].should_update || false,
        reason: sourcesData[source].reason,
      }));

      // Transform schedule object to schedule array
      const scheduleData = scheduleRes.data.schedule || {};
      const scheduleArray = Object.keys(scheduleData).map((source) => ({
        source,
        interval_hours: scheduleData[source].update_interval_hours || null,
        auto_update:
          scheduleData[source].should_update !== undefined
            ? !scheduleData[source].reason?.includes("Manual")
            : true,
        description: scheduleData[source].reason || "",
      }));

      setLists(listsArray);
      setSchedule(scheduleArray);
    } catch (error) {
      console.error("Failed to load data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleUpdate = async (source) => {
    setUpdating((prev) => ({ ...prev, [source]: true }));
    try {
      await sanctionsAPI.updateList(source, true);
      await loadData();
    } catch (error) {
      console.error(`Failed to update ${source}:`, error);
      alert(`Failed to update ${source}. Please check console for details.`);
    } finally {
      setUpdating((prev) => ({ ...prev, [source]: false }));
    }
  };

  const handleUpdateAll = async () => {
    setUpdating({ all: true });
    try {
      await sanctionsAPI.updateAllLists();
      await loadData();
      alert("All lists updated successfully!");
    } catch (error) {
      console.error("Failed to update all lists:", error);
      alert("Failed to update some lists. Please check console for details.");
    } finally {
      setUpdating({ all: false });
    }
  };

  const getStatusColor = (needsUpdate) => {
    return needsUpdate ? "yellow" : "green";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="animate-spin text-primary-600" size={48} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Lists Management</h1>
        <button
          onClick={handleUpdateAll}
          disabled={updating.all}
          className="btn-primary flex items-center space-x-2 disabled:opacity-50"
        >
          <RefreshCw size={18} className={updating.all ? "animate-spin" : ""} />
          <span>{updating.all ? "Updating All..." : "Update All Lists"}</span>
        </button>
      </div>

      {/* Lists Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {lists.map((list) => {
          const scheduleInfo = schedule.find((s) => s.source === list.source);
          const color = getStatusColor(list.needs_update);

          return (
            <div
              key={list.source}
              className="card hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-xl font-bold">{list.source}</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {list.count?.toLocaleString() || 0} entities
                  </p>
                </div>
                <div className={`w-3 h-3 rounded-full bg-${color}-500`} />
              </div>

              <div className="space-y-2 mb-4">
                <div className="flex items-center text-sm text-gray-600">
                  <Calendar size={16} className="mr-2" />
                  <span>
                    Last:{" "}
                    {list.last_update
                      ? new Date(list.last_update).toLocaleString()
                      : "Never"}
                  </span>
                </div>

                {scheduleInfo && (
                  <div className="text-sm text-gray-600">
                    <span className="font-medium">Interval:</span>{" "}
                    {scheduleInfo.interval_hours}h{" "}
                    {scheduleInfo.auto_update && "(Auto)"}
                  </div>
                )}

                {list.needs_update && (
                  <div className="flex items-center text-sm text-yellow-600">
                    <AlertCircle size={16} className="mr-2" />
                    <span>Update recommended</span>
                  </div>
                )}
              </div>

              <button
                onClick={() => handleUpdate(list.source)}
                disabled={updating[list.source]}
                className="w-full btn-primary disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                <RefreshCw
                  size={16}
                  className={updating[list.source] ? "animate-spin" : ""}
                />
                <span>
                  {updating[list.source] ? "Updating..." : "Update Now"}
                </span>
              </button>
            </div>
          );
        })}
      </div>

      {/* Update Schedule */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Update Schedule</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                  Source
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">
                  Interval
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
              {schedule.map((item) => (
                <tr key={item.source} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{item.source}</td>
                  <td className="px-4 py-3">{item.interval_hours} hours</td>
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
    </div>
  );
}
