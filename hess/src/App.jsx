import React, { useRef, useState } from 'react';
import { Chessboard } from 'react-chessboard';

import CssBaseline from '@mui/material/CssBaseline';
import Container   from '@mui/material/Container';

import BoardView from './components/BoardView';
import NavBar from './components/NavBar';


function App() {

  return (
    <React.Fragment>
      <CssBaseline />
      <NavBar />
      <Container maxWidth='lg' height="100vh">
        {/* App bar here */}
        <BoardView />
      </Container>
    </React.Fragment>
  );
}

export default App;
