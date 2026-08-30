// LA PORTE serveur du container peinture (docs/organisation.md §2) : portraits
// et voix, lus par les autres containers — jamais en direct.
module.exports = {
  portraits: require("../portraits"),     // teintes et fraicheur des portraits
  voix: require("../voix"),               // le journal des voix et le port
  routeVoix: require("../routes/voix"),   // /voix/*
  medias: require("../routes/medias"),    // /retrospective, /medailles, captures, sons
};
