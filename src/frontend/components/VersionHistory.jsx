import React from 'react';

function VersionHistory({ versions, onSelectVersion }) {
  return (
    <div className="version-history">
      <h2>Version History</h2>
      <ul>
        {versions.map((version, index) => (
          <li key={version.id} onClick={() => onSelectVersion(version)}>
            Version {index + 1} - {version.timestamp}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default VersionHistory;
