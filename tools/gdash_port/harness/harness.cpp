// Command-line GDash replay player, for checking our port against the original engine. GPL-3.0-or-later.
// Built by build.sh against the reference checkout; prints one line per replay.
#include "config.h"
#include <glib.h>
#include <cstdio>
#include <fstream>
#include <sstream>
#include "cave/caveset.hpp"
#include "cave/cavestored.hpp"
#include "cave/caverendered.hpp"
#include "cave/helper/cavereplay.hpp"
#include "fileops/bdcffload.hpp"
#include "misc/logger.hpp"

void gd_cave_types_init();
void gd_cave_objects_init();

int main(int argc, char **argv) {
    Logger logger(true);
    gd_cave_types_init();
    gd_cave_objects_init();
    std::ifstream f(argv[1]);
    std::stringstream ss; ss << f.rdbuf();
    CaveSet cs = load_from_bdcff(ss.str().c_str());
    int trace_cave = argc > 2 ? atoi(argv[2]) : -1;
    for (unsigned ci = 0; ci < cs.caves.size(); ++ci) {
        CaveStored &cave = cs.cave(ci);
        for (std::list<CaveReplay>::iterator it = cave.replays.begin(); it != cave.replays.end(); ++it) {
            CaveReplay &r = *it;
            CaveRendered c(cave, r.level - 1, r.seed);
            c.setup_for_game();
            r.rewind();
            int score = 0, frames = 0, nomore = 0;
            while (c.player_state != GD_PL_TIMEOUT && frames < 100000) {
                GdDirectionEnum mv = MV_STILL; bool fire = false, suicide = false;
                if (!r.get_next_movement(mv, fire, suicide)) { if (++nomore > 15) break; mv = MV_STILL; fire = suicide = false; }
                c.iterate(mv, fire, suicide);
                frames++;
                score += c.score;
                if ((int)ci == trace_cave) printf("F %d speed %d time %d ck %d\n", frames, (int)c.speed, (int)c.time, (int)c.ckdelay_current);
                if (c.player_state == GD_PL_EXITED) {
                    while (c.time > 0) {
                        if (c.time > 60 * c.timing_factor) { c.time -= 9 * c.timing_factor; score += c.timevalue * 9; }
                        else { c.time -= c.timing_factor; score += c.timevalue; }
                        if (c.time < 0) c.time = 0;
                    }
                    break;
                }
            }
            printf("%s | %s L%d: got %s %d, expected %s %d (%d frames)\n", (score == r.score && (c.player_state == GD_PL_EXITED) == (bool)r.success) ? "OK " : "BAD",
                   cave.name.c_str(), (int)r.level, c.player_state == GD_PL_EXITED ? "true" : "false", score, r.success ? "true" : "false", (int)r.score, frames);
        }
    }
    return 0;
}
