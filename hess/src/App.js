import React, { useRef, useState } from 'react';
import { Chessboard } from 'react-chessboard';


function App() {

  const [game, setGame] = useState("");

  return (
    <div className="App">
      <Chessboard 
        id="BasicBoard"
        
      />
    </div>
  );
}

export default App;
