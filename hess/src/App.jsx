import React, { useRef, useState } from 'react';
import { Chessboard } from 'react-chessboard';

import CssBaseline from '@mui/material/CssBaseline';
import Container   from '@mui/material/Container';

import BoardView from './components/BoardView';


function App() {

  return (
    <React.Fragment>
      <CssBaseline />
      <Container maxWidth='lg'>
        {/* App bar here */}
        <BoardView />
      </Container>
    </React.Fragment>
  );
}

export default App;
