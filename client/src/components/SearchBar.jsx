import React, { useState } from 'react';

function SearchBar({ onSearch }) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(query);
  };

  return (
    <div className="search-container">
      <form className="search-form" onSubmit={handleSubmit}>
        <input
          type="text"
          className="search-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter Ticker or Company Name (e.g. NVDA)..."
        />
        <button type="submit" className="search-button">
          ANALYZE
        </button>
      </form>
    </div>
  );
}

export default SearchBar;
