import React, { useRef, useState } from 'react';
import { Chessboard, Chess } from 'react-chessboard';


function App() {

  const [game, setGame] = useState(new Chess());

  return (
    <div className="App">
      <Chessboard 
        id="BasicBoard"
        
      />
    </div>
  );
}

export default App;
